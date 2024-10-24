"""
These classes must only ever contain "immutable" data.

We never want to worry about the state of these objects at any point during a patch injection.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Optional, Set, Tuple
from warnings import warn

from ofrak_patch_maker.toolchain.model import Segment, BinFileType
from ofrak_type.symbol_type import LinkableSymbolType

AUTOGENERATE_WARNING = """/*
*
* WARNING: DO NOT EDIT THIS FILE MANUALLY
*      This is an autogenerated file
*
*/

"""


class PatchMakerException(Exception):
    pass


@dataclass(frozen=True)
class AssembledObject:
    """
    The result of any `compile` or `assemble` step

    :var path: .o file path
    :var file_format: .elf, .coff, etc.
    :var segment_map: e.g. `{".text", Segment(...)}`
    :var strong_symbols:
    :var unresolved_symbols: {symbol name: (address, symbol type)}
    :var bss_size_required: DEPRECATED
    """

    path: str
    file_format: BinFileType
    segment_map: Mapping[str, Segment]  # segment name to Segment
    strong_symbols: Mapping[str, Tuple[int, LinkableSymbolType]]
    unresolved_symbols: Mapping[str, Tuple[int, LinkableSymbolType]]
    bss_size_required: Optional[int] = None

    def __post_init__(self):
        if self.bss_size_required is not None:
            warn("AssembledObject.bss_size_required is deprecated")


@dataclass(frozen=True)
class LinkedExecutable:
    """
    The result of any `link` step.

    :var path: executable file path
    :var file_format: .elf, .coff, etc.
    :var segments: the segments contained in this executable
    :var symbols: the global function and data symbol mapping information for this executable
    :var relocatable: TODO: whether or not the executable is relocatable
    """

    path: str
    file_format: BinFileType
    segments: Tuple[Segment, ...]
    symbols: Mapping[str, Tuple[int, LinkableSymbolType]]
    relocatable: bool


@dataclass(frozen=True)
class PatchRegionConfig:
    """
    PatchRegionConfig is the dataclass required to generate an .ld script. That describes
    a set of code and data patches.

    For every available object file, new code and data Segments are populated with the
    target VM addresses/sizes within the client firmware.

    [PatchMaker][ofrak_patch_maker.patch_maker.PatchMaker] uses this information to generate memory
    regions and the sections that will go into those memory regions.

    :var patch_name: a name
    :var segments: {object file path: Tuple of Segments}
    """

    patch_name: str
    segments: Mapping[str, Tuple[Segment, ...]]


@dataclass(frozen=True)
class FEM:
    """
    "FEM" stands for Final Executable and Metadata

    Keeping this class frozen ensures we have a hash for every instance

    Instances of this class should never be declared outside of
    [PatchMaker][ofrak_patch_maker.patch_maker.PatchMaker].

    :var name:
    :var executable:
    """

    name: str
    executable: LinkedExecutable


@dataclass(frozen=True)
class BOM:
    """
    "BOM" stands for Batched Objects and Metadata

    Keeping this class frozen ensures we have a hash for every instance.

    Instances of this class should never be declared outside of
    [PatchMaker][ofrak_patch_maker.patch_maker.PatchMaker].

    :var name: a name
    :var object_map: {source file path: AssembledObject}
    :var unresolved_symbols: symbols used but undefined within the BOM source files
    :var bss_size_required: DEPRECATED
    :var entry_point_symbol: symbol of the patch entrypoint, when relevant
    """

    name: str
    object_map: Mapping[str, AssembledObject]
    unresolved_symbols: Set[str]
    bss_size_required: Optional[int]
    entry_point_symbol: Optional[str]
    segment_alignment: int

    def __post_init__(self):
        if self.bss_size_required is not None:
            warn("BOM.bss_size_required is deprecated")


class SourceFileType(Enum):
    DEFAULT = 0
    C = 1
    ASM = 2
