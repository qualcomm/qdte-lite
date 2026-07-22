# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Parse user-typed property text into DTOperation value payloads.

Per-type contracts (matching what qdte.core.dtwrapper accepts):
  WORDS   -> list of raw token strings; core coerces each via int(tok, 0),
             so 0x.../0o.../0b.../decimal all work.  Tokens are
             pre-validated here to give immediate feedback.
  BYTES   -> list[int] in [0, 255].
  STRINGS -> list[str], parsed from the single-quoted space-delimited
             form shared with the tkinter editor (qdte.core.strvalues).
  EMPTY   -> no value; empty properties are not editable.
"""

from qdte.core.dtwrapper import FdtPropertyType
from qdte.core.strvalues import string_to_strarray

UINT32_MAX = 0xFFFFFFFF
BYTE_MAX = 0xFF


def parse_value(prop_type, text):
    """Convert editor text into the value payload for EDIT_PROPERTY_VALUE.

    Raises ValueError with a user-presentable message on invalid input.
    """
    if prop_type == FdtPropertyType.WORDS:
        tokens = text.split()
        if not tokens:
            raise ValueError("WORDS value must contain at least one number")
        for tok in tokens:
            try:
                val = int(tok, 0)
            except ValueError:
                raise ValueError(
                    "Not a number: %r (use decimal or 0x/0o/0b prefixed literals)" % tok
                ) from None
            if not 0 <= val <= UINT32_MAX:
                raise ValueError("%r is outside the uint32 range" % tok)
        return tokens
    if prop_type == FdtPropertyType.BYTES:
        tokens = text.split()
        if not tokens:
            raise ValueError("BYTES value must contain at least one byte")
        out = []
        for tok in tokens:
            try:
                val = int(tok, 0)
            except ValueError:
                raise ValueError("Not a number: %r" % tok) from None
            if not 0 <= val <= BYTE_MAX:
                raise ValueError("%r is outside the byte range" % tok)
            out.append(val)
        return out
    if prop_type == FdtPropertyType.STRINGS:
        return string_to_strarray(text)
    raise ValueError(
        "Properties of type %s have no editable value"
        % getattr(prop_type, "name", prop_type)
    )


def default_value(prop_type):
    """Initial value payload for a newly added property of prop_type.

    Unlike EDIT_PROPERTY_VALUE (which coerces WORDS string tokens),
    ADD_PROPERTY hands the value straight to the pyfdt constructors, so
    WORDS/BYTES must be real ints here.
    """
    return {
        FdtPropertyType.WORDS: [0],
        FdtPropertyType.BYTES: [0],
        FdtPropertyType.STRINGS: ["value"],
    }.get(prop_type)
