# notification/services/__init__.py
# Exposes the public service-layer API so callers only need to import from
# `notification.services` rather than digging into sub-modules.

from .dispatcher import trigger_event  # noqa: F401

__all__ = ["trigger_event"]
