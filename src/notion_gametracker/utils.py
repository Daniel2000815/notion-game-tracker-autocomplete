"""
This module provides a utility function to recursively remove commas from various data types.

The `remove_comas` function can handle strings, lists, dictionaries, and objects with 
`_fields` attributes (typically data classes or named tuples), removing commas from all of them.

Functions:
- remove_comas: Recursively removes commas from strings, lists, dictionaries,
or objects with `_fields`.
"""
def remove_comas(val):
    """
    Recursively removes commas from strings, lists, dictionaries,
    or objects with _fields attributes.

    Args:
    - val (str, list, dict, object): The input value from which commas should be removed.
    The function will handle:
        - Strings: Removes commas from the string.
        - Lists: Recursively processes each item in the list.
        - Dictionaries: Recursively processes each value in the dictionary.
        - Objects with _fields attribute: Recursively processes each field in the object.
    """
    if isinstance(val, str):
        return val.replace(",", "")

    if isinstance(val, list):
        return [remove_comas(item) for item in val]

    if isinstance(val, dict):
        return {key: remove_comas(subvalor) for key, subvalor in val.items()}

    if hasattr(val, "_fields"):
        return val.__class__(**{field: remove_comas(getattr(val, field)) for field in val._fields})

    return val
