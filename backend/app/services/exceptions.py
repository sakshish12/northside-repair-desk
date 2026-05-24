class SlotConflictError(Exception):
    """Another confirmed appointment overlaps this resource interval."""


class NotFoundError(Exception):
    """Entity not found."""


class ValidationError(Exception):
    """Invalid input for booking."""
