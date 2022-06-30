import re
from typing import Union


def is_matching(item_dict: dict, filter_dict: dict) -> bool:
    """
    Checks if each (key, value) pair in filter_dict matches its corresponding (key, value) pair in item_dict.

    Parameters
    ----------
    item_dict : dict
        Main dictionary to be matched with a filter_dict
    filter_dict : dict
        Filter dictionary used to restrict to specific values

    Returns
    -------
    bool
    - True => if (key, value) pair in filter_dict matches (key, value) pair in item_dict
    - False => if one or more (key, value) pair(s) don't match

    Notes
    -----
    - an empty filter_dict matches every item_dict
    - matching is done either by a <string>==<string> or a regex.search(<regexobj>, <string>)
    """
    matching = True
    for key, fvalue in filter_dict.items():
        ivalue = item_dict.get(key, "")  # Get the items value an empty string
        if isinstance(fvalue, re.Pattern):
            matching = (re.search(fvalue, ivalue) != None)  # True, if a match object is returned
        else:  # Match by string compare
            matching = str(fvalue) == str(ivalue)
        if not matching:  # Only returns true if all items match
            break
    return matching


def is_equal_parameterized(string_par: str, string_val: str) -> bool:
    """
    Checks if two string are the same if one of them has parameters replaced by values, and the other one has the placeholders.
    For parameters in Gherkin TestCases
    
    Parameters
    ----------
    string_par : str
        String with parameters marked like '{parameter}'
    string_val : str
        String which might be the same but has values instead of placeholders

    Returns
    -------
    bool
    - True => if both strings are equal
    - False => if the strings are not equal
    """
    string_par = re.sub('\\.', "\\.",
                        string_par)  # replace single dots which would be read as wildcard with a escaped dot
    pattern = re.sub('\{.*\}', '(.*)', string_par)  # type: ignore

    if re.fullmatch(pattern, string_val):
        return True

    return False


def is_equal_ignore_separators(string1: str, string2: str) -> bool:
    """
    Checks if two string are the same if you ignore both upper and lower case, as well as spaces, hyphens and underscores.

    Parameters
    ----------
    string1 : str
        First string
    string2 : str
        Second string

    Returns
    -------
    bool
    - True => if both strings are equal
    - False => if the strings are not equal
    """
    cmp1 = string1.replace(" ", "").replace("-", "").replace("_", "").upper()
    cmp2 = string2.replace(" ", "").replace("-", "").replace("_", "").upper()
    return (cmp1 == cmp2)


def stringToBoolean(boolean: str) -> Union[bool, None]:
    """
    Turns a string representation of a boolean expression into a boolean.

    Parameters
    ----------
    boolean : str
        String representation of a boolean expression

    Returns
    -------
    bool
    - True => if string matches one of the True values
    - False => if string matches one of the False values
    - None => if string matches neither True nor False values

    Notes
    -----
    True values are: "True, true, T, t, 1, Yes, yes, Y, y"
    False values are: "False, false, F, f, 0, No, no, N, n" 
    """
    if boolean in ("True", "true", "T", "t", "1", "Yes", "yes", "Y", "y"):
        return True
    elif boolean in ("False", "false", "F", "f", "0", "No", "no", "N", "n"):
        return False
    else:
        return None
