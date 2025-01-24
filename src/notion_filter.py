"""
Create and manage filters for querying Notion's API.
It defines a mapping of Notion property types and provides helper functions for building
filter parameters to interact with Notion's database through its API.

Functions:
- new_filter: Creates a filter for a specific property with a given action and value.
- generate_filter_params: Generates the full parameters for making a filtered API
request with optional pagination.

Notion Property Types:
- A dictionary that maps common property names to their corresponding Notion
data types (e.g., select, multi_select, date).
"""

import re

notion_property_types = {
    "Anticipated": "select",
    "Created time": "created_time",
    "Complete Date": "date",
    "Catalog": "multi_select",
    "Rating": "number",
    "Playtime": "number",
    "Platform": "multi_select",
    "IGDB ID": "number",
    "Genre": "multi_select",
    "IGDB Rating": "number",
    "Stats": "relation",
    "HLTB": "number",
    "Franchise": "multi_select",
    "Launch Date": "date",
    "Status": "select",
    "Additional Labels": "multi_select",
    "Start Date": "date",
    "Developer": "multi_select",
    "Game Title": "rich_text"
}

def new_filter(property_name, filter_action, property_value):
    """
    Creates a filter for a specific Notion property based on the provided filter action and value.

    Args:
    - property_name (str): The name of the Notion property to filter by.
    - filter_action (str): The action for the filter (e.g., "equals", "greater_than").
    - property_value (str): The value for the filter (can be a string, boolean, or integer).

    Returns:
    - dict: A dictionary representing the filter to be used in a Notion API request.

    Example:
    new_filter("Rating", "equals", 5)
    Would return:
    {
        "property": "Rating",
        "number": {"equals": 5}
    }
    """
    if property_value in ('True', 'False'):
        property_value = bool(property_value)

    elif bool(re.match(r"^[0-9]+$", property_value)):
        property_value = int(property_value)

    return {
        "property": property_name,
        notion_property_types[property_name]: {filter_action: property_value}
    }

def generate_filter_params(filters, page_amount=25):
    """
    Generates the full parameters for making a filtered API request, with optional pagination.

    Args:
    - filters (list): A list of filter dictionaries, where each dictionary is
    a filter created by `new_filter`.
    - page_amount (int, optional): The number of results per page. Defaults to 25.

    Returns:
    - dict: The full set of parameters for the Notion API request, including
    the filters and pagination information.

    Example:
    generate_filter_params([{"property": "Rating", "number": {"equals": 5}}], page_amount=10)
    Would return:
    {
        "page_size": 10,
        "filter": {"property": "Rating", "number": {"equals": 5}}
    }
    """
    params = {"page_size": page_amount}

    if filters:
        if len(filters) == 1:
            params["filter"] = filters[0]
        else:
            params["filter"] = {"and": filters}

    return params
