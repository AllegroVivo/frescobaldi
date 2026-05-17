from __future__ import annotations

from typing import Union, Literal, Protocol


class Translatable(Protocol):
    def translateUI(self) -> None: ...


_CommonEncodings = Literal[
    "utf-8",
    "utf-16",
    "latin-1",
    "ascii",
    "cp1252"
]
Encoding = Union[_CommonEncodings, str]

_CommonExtensions = Literal[
    ".ly", ".lyi", ".ily",
    ".tex", ".lytex", ".latex",
    ".docbook", ".lyxml",
    ".html", ".xml",
    ".itely", ".tely", ".texi", ".texinfo",
    ".scm"
]
FileExtension = Union[_CommonExtensions, str]

_MusicFonts = Literal[
    "Helsinki", "Helsinki Std", "Helsinki Text Std",
    "Opus", "Opus Std", "Opus Text Std", "Opus Chords Std",
    "Inkpen2 Std", "Inkpen2 Text Std", "Inkpen2 Script Std",
    "Reprise Std", "Reprise Text Std", "Reprise Script Std"
]
_TextFonts = Literal[
    "Times New Roman",
    "Georgia",
    "Garamond",
    "Century",
    "Century Schoolbook",
    "Bookman Old Style",
    "Palatino Linotype"
]
_SansFonts = Literal[
    "Arial",
    "Calibri",
    "Segoe UI",
    "Tahoma",
    "Trebuchet MS",
    "Verdana",
    "Century Gothic"
]
_MonoFonts = Literal[
    "Consolas",
    "Courier New",
    "Cascadia Code",
    "Cascadia Mono",
    # "Lucida Console"  - Avoid because of no bold weight support.
]
Font = Union[
    _MusicFonts,
    _TextFonts,
    _SansFonts,
    _MonoFonts,
    str
]
