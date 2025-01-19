def removeComas(val):
    if isinstance(val, str):
        return val.replace(",", "")
    elif isinstance(val, list):
        return [removeComas(item) for item in val]
    elif isinstance(val, dict):
        return {key: removeComas(subvalor) for key, subvalor in val.items()} 
    elif hasattr(val, "_fields"):
        return val.__class__(**{field: removeComas(getattr(val, field)) for field in val._fields}) 
    else:
        return val
 