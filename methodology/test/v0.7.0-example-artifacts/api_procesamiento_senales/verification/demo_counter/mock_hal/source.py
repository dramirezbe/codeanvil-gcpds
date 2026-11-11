def samples(count: int):
    """Independent synthetic generator with the declared three-value period."""
    for index in range(count):
        yield (0.0, 1.0, 2.0)[index % 3]
