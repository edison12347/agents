class BuilderError(Exception):
    """Base error for Builder."""


class AuthError(BuilderError):
    """Raised when execution backend CLI auth is missing."""


class SecretError(BuilderError):
    """Raised when Doppler access or required variables fail."""


class ReleaseError(BuilderError):
    """Raised when git release flow fails."""


class ValidationError(BuilderError):
    """Raised when config/spec validation fails."""
