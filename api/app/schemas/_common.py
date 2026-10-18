def reject_null_fields(model, *fields):
    """PATCH models: omitted = unchanged, but an explicit null on a NOT NULL field is an error."""
    for f in fields:
        if f in model.model_fields_set and getattr(model, f) is None:
            raise ValueError(f"{f} cannot be null")
    return model