"""Shared file-upload validators — used by any app with a FileField (laboratory reports, message
attachments). Kept at the project level since neither app "owns" the concept of an upload limit."""
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class MaxFileSizeValidator:
    """Rejects uploads over `max_mb` megabytes. Class-based (not a closure) so Django can serialize
    it into migration files via @deconstructible."""

    def __init__(self, max_mb):
        self.max_mb = max_mb

    def __call__(self, file):
        max_bytes = self.max_mb * 1024 * 1024
        if file.size > max_bytes:
            raise ValidationError(f"File too large — maximum size is {self.max_mb}MB.")

    def __eq__(self, other):
        return isinstance(other, MaxFileSizeValidator) and self.max_mb == other.max_mb
