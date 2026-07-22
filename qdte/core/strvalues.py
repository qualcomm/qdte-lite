# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Text <-> value helpers for STRINGS-type DT properties.

Shared by the GUI and any other caller so a typed value parses the same
everywhere.  Historically these lived in the tkinter
editview module.
"""

import string


def int_allow_blank(nbrstr, base=10):
    """Helper function to convert a string to an int, but allow blanks (blank = 0)

    This helper function is a simple wrapper around the int() call, but iwth the difference that, if the string is
    empty, it will simply return 0. It is used by the functions that split an string of space-separated values into an
    array of ints, in order to prevent raising errors for empty strings that might occur if the user is trying to type
    in a new value.

    :param nbrstr: The number string to parse
    :param base: The base that `nbrstr` is in. Defaults to base 10.
    :return: The integer value of nbrstr (blank = 0)
    """

    return 0 if len(nbrstr) == 0 else int(nbrstr, base)


def strarray_to_string(arr):
    """Convert an array of strings into a single single-quote space-delimited string

    This function converts a list of strings into a single string. To do so, it first escapes the string where necessary
    (the characters that are escaped are the backslash, single quote, and tab), and then encloses the escaped string in
    single quotes, and finally joins the entire string list with spaces such that each string is separated by a space.
    For example, given a user input list ["one'", "two"], the output will be the string "'one\'' 'two'".

    This function is the counterpart/does the opposite of string_to_strarray(), although string_to_strarray() is capable
    of parsing a wider range of inputs than this function produces (e.g. two spaces separating different strings is
    fine for string_to_strarray(), but this function will not do that).

    :param arr: list of strings
    :return: string representing the given `arr`
    """

    def escape_helper(mystr):
        """helper function to escape the characters that need escaping"""

        # things that need to be escaped (use this order so that we don't replace \t into \\\\t)
        mystr = mystr.replace("\\", "\\\\")
        mystr = mystr.replace("'", "\\'")
        mystr = mystr.replace("\t", "\\t")
        return mystr

    # escape each string and add the single quotes around it
    ret = ["'" + escape_helper(elem) + "'" for elem in arr]

    # the output of this function is a string in the format 'str\t1\'' 'str\n2' '\\str_3'
    return " ".join(ret)


def string_to_strarray(mystr):
    """Parse a single string of single-quoted space-delimited values into an array of strings

    :param mystr: string of single-quoted space-delimited values
    :return: list of strings representing the unescaped and parsed value of `mystr`
    """

    # parser flags, etc.
    seek_string_start = True
    escape_next = False
    ret = []
    str_start_pos = 0

    # rudimentary parser to filter out the start and end of a string (quotes) while ignoring escape sequences
    for i in range(0, len(mystr)):
        if seek_string_start:
            # only three characters are allowed in here: ', (last one is a space)
            if mystr[i] == "," or mystr[i] == " ":
                continue
            elif mystr[i] == "'":
                # found the start of a string, so store it, and switch to looking for the end of a string instead
                seek_string_start = False
                str_start_pos = i + 1
            else:
                # parse error
                raise ValueError(
                    "string_to_strarray() Parse error: expected double-quote, comma, or space, but got "
                    "%s instead!" % mystr[i]
                )
        else:
            if escape_next:
                # wanted to escape the last character, so we escape it and continue
                # note that we don't actually replace in the input string yet - we do this later
                escape_next = False
                continue
            if mystr[i] == "\\":
                # backslash = escaping the next character
                escape_next = True
            elif mystr[i] == "'":
                # found the end of a string; it goes from str_start_pos to i (inclusive)
                str_dat = mystr[str_start_pos:i]

                # parse out the representation
                # again, order matters! otherwise we could accidentally introduce escape sequences
                str_dat = str_dat.replace("\\\\", "\\")
                str_dat = str_dat.replace("\\'", "'")
                str_dat = str_dat.replace("\\t", "\t")

                # all good
                ret.append(str_dat)
                seek_string_start = True
            elif mystr[i] not in string.printable or mystr[i] in ("\r", "\n"):
                # check that this character is valid
                raise ValueError(
                    "string_to_strarray() error: Illegal character at position %d: %s"
                    % (i, mystr[i])
                )

    if escape_next or (not seek_string_start):
        # still looking to escape something or for the end of a string, so something has gone wrong
        raise ValueError("Unexpected end of input when parsing")

    if len(ret) == 0 or any([True for mystr in ret if len(mystr) == 0]):
        # one of the strings was empty
        raise ValueError("STRINGS values are not permitted to be empty!")

    # all good!
    return ret
