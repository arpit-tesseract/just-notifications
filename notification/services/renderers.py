"""
notification/services/renderers.py
====================================
Phase 3 — The Renderer (Strategy Pattern).

Templates stored in ``NotificationTemplate.content`` / ``.title`` are plain
Django template strings (e.g. ``"Hello {{ user_name }}, your plan is
{{ plan_name }}."``).  This module provides a family of renderer classes
that use Django's built-in ``Template`` + ``Context`` engine to interpolate
``context_data`` into those strings.

Using the Strategy Pattern means:

* Callers depend only on the ``BaseRenderer`` interface.
* Swapping or extending rendering behaviour (e.g. adding an SMS renderer that
  strips HTML) requires no changes to orchestration code.
* Each renderer can apply channel-specific pre/post-processing (e.g.
  ``EmailRenderer`` could inline CSS in future).

Pipeline position
-----------------
    process_event_task
          │
          ▼
    renderer.render(template_str, context_data)   ← this module
          │
          ▼
    Notification.objects.create(title=..., content=...)
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from django.template import Context, Template

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class BaseRenderer(ABC):
    """Abstract base class for all notification template renderers.

    All concrete renderers **must** implement :meth:`render`.  The base class
    itself can also perform shared pre-processing (e.g. sanitising the context
    dict) before delegating to the subclass.

    Subclasses
    ----------
    * :class:`EmailRenderer` — renders HTML/plain-text email templates.
    * :class:`PushRenderer`  — renders short push-notification strings.
    """

    def render(self, template_str: str, context_data: dict[str, Any]) -> str:
        """Interpolate ``context_data`` into ``template_str`` and return the result.

        Parameters
        ----------
        template_str:
            A raw Django template string, e.g.
            ``"Dear {{ user_name }}, your invoice of ₹{{ amount }} is due."``
        context_data:
            Key/value pairs to be injected into the template.  Must be
            JSON-serialisable (strings, numbers, booleans, None).

        Returns
        -------
        str
            The fully rendered string with all ``{{ variable }}`` tokens
            replaced by their values.  Unknown variables are silently replaced
            with an empty string (Django's default behaviour).

        Notes
        -----
        *Template compilation* is intentionally not cached here; for
        high-volume workloads consider wrapping the ``Template`` object in
        ``functools.lru_cache`` keyed on the template PK + updated_at.
        """
        safe_context = self._sanitise_context(context_data)
        return self._do_render(template_str, safe_context)

    # ------------------------------------------------------------------
    # Hook for subclasses
    # ------------------------------------------------------------------

    @abstractmethod
    def _do_render(self, template_str: str, context_data: dict[str, Any]) -> str:
        """Channel-specific rendering logic implemented by each subclass.

        Subclasses receive the already-sanitised context dict.
        """

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sanitise_context(context_data: dict[str, Any]) -> dict[str, Any]:
        """Return a safe copy of ``context_data`` with non-string values coerced.

        Converts any non-string leaf values to their ``str()`` representation
        so Django's template engine never raises ``VariableDoesNotExist`` on
        unexpected types.
        """
        return {k: str(v) if not isinstance(v, str) else v for k, v in context_data.items()}


# ---------------------------------------------------------------------------
# Concrete renderers
# ---------------------------------------------------------------------------

class EmailRenderer(BaseRenderer):
    """Renderer for email notifications.

    Delegates rendering to Django's template engine so all standard template
    tags (``{% if %}``, ``{% for %}``, etc.) work out of the box.  In future
    this renderer could also inline CSS or convert Markdown to HTML.

    Usage
    -----
    >>> renderer = EmailRenderer()
    >>> body = renderer.render(
    ...     "Dear {{ user_name }}, your plan {{ plan_name }} renews on {{ date }}.",
    ...     {"user_name": "Alice", "plan_name": "Pro", "date": "2026-06-01"},
    ... )
    'Dear Alice, your plan Pro renews on 2026-06-01.'
    """

    def _do_render(self, template_str: str, context_data: dict[str, Any]) -> str:
        """Render ``template_str`` using Django's full template engine.

        Supports all standard Django template tags and filters in addition to
        simple variable substitution.

        Parameters
        ----------
        template_str:
            Raw Django template string.
        context_data:
            Pre-sanitised context dict from :meth:`BaseRenderer.render`.

        Returns
        -------
        str
            Rendered output string.
        """
        try:
            tmpl = Template(template_str)
            ctx = Context(context_data)
            return tmpl.render(ctx)
        except Exception:
            logger.exception(
                "EmailRenderer._do_render: failed to render template; "
                "returning raw template_str as fallback."
            )
            return template_str


class PushRenderer(BaseRenderer):
    """Renderer for push / in-app notifications.

    Push messages must be short (≤ 200 chars in most gateway limits).  This
    renderer applies the same Django template interpolation as
    :class:`EmailRenderer` and then truncates the result to 200 characters
    with an ellipsis if needed.

    Usage
    -----
    >>> renderer = PushRenderer()
    >>> msg = renderer.render(
    ...     "New message from {{ sender_name }}",
    ...     {"sender_name": "Bob"},
    ... )
    'New message from Bob'
    """

    #: Maximum character length for push notification bodies.
    MAX_LENGTH: int = 200

    def _do_render(self, template_str: str, context_data: dict[str, Any]) -> str:
        """Render and truncate to :attr:`MAX_LENGTH` characters.

        Parameters
        ----------
        template_str:
            Raw Django template string.
        context_data:
            Pre-sanitised context dict from :meth:`BaseRenderer.render`.

        Returns
        -------
        str
            Rendered string, truncated to ``MAX_LENGTH`` chars if necessary.
        """
        try:
            tmpl = Template(template_str)
            ctx = Context(context_data)
            result: str = tmpl.render(ctx)
        except Exception:
            logger.exception(
                "PushRenderer._do_render: failed to render template; "
                "returning raw template_str as fallback."
            )
            result = template_str

        if len(result) > self.MAX_LENGTH:
            logger.debug(
                "PushRenderer._do_render: truncating rendered string from "
                "%d to %d chars.",
                len(result),
                self.MAX_LENGTH,
            )
            return result[: self.MAX_LENGTH - 1] + "…"

        return result
