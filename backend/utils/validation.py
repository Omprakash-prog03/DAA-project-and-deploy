def validate_coordinates(lat: float, lon: float) -> bool:
    """Ensures latitude is in [-90, 90] and longitude is in [-180, 180]."""
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0

def validate_positive(value: float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be strictly positive (got {value}).")

