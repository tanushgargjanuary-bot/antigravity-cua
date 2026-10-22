"""Exceptions for Antigravity CUA Bridge."""

class CuaError(Exception):
    """Base exception for all Antigravity CUA errors."""
    pass

class SandboxNotFoundError(CuaError):
    """Raised when a requested sandbox cannot be found or has expired."""
    pass

class LeaseExpiredError(CuaError):
    """Raised when an operation is attempted on an expired sandbox lease."""
    pass

class SpacesDConnectionError(CuaError):
    """Raised when communication with the guest cua-spacesd daemon fails."""
    pass

class CommandExecutionTimeout(CuaError):
    """Raised when a remote command exceeds its execution deadline."""
    pass

class IsolationPolicyViolation(CuaError):
    """Raised when an action attempts to violate the host GUI isolation invariant."""
    pass
