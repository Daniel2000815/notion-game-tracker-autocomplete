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

def newFilter(property_name, filter_action, property_value):
    if property_value=="True" or property_value=="False":
        property_value = bool(property_value)

    print({
        "property": property_name,
        notion_property_types[property_name]: {filter_action: property_value}
    })
    return {
        "property": property_name,
        notion_property_types[property_name]: {filter_action: property_value}
    }

def generateFilterParams(filters, pageAmount=100):
    params = {"page_size": pageAmount}

    if filters:
        if len(filters) == 1:
            params["filter"] = filters[0]
        else:
            params["filter"] = {"and": filters}

    return params
