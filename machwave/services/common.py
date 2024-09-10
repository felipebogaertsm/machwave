def obtain_attributes_from_object(obj) -> dict:
    try:
        return vars(obj)
    except TypeError:  # if does not have __dict__ method
        return {}
