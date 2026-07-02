import re
from typing import Dict, Any
from django.core.exceptions import ObjectDoesNotExist
from ..models import NotificationTemplate


class TemplateServiceError(Exception):
    """Base exception for all template service errors."""
    pass


class TemplateRenderingError(TemplateServiceError):
    """Exception raised when rendering a template fails (e.g. missing variables)."""
    pass


class TemplateService:
    """
    Service responsible for managing, validating, and rendering notification templates.
    """

    @staticmethod
    def get_template_by_code(code: str) -> NotificationTemplate:
        """
        Fetches a NotificationTemplate from the database by its unique code.

        Args:
            code (str): The template identifier.

        Returns:
            NotificationTemplate: The retrieved template instance.

        Raises:
            TemplateServiceError: If the template does not exist.
        """
        if not code:
            raise TemplateServiceError("Template code must be a non-empty string.")

        try:
            return NotificationTemplate.objects.select_related('category', 'priority').get(code=code)
        except ObjectDoesNotExist as e:
            raise TemplateServiceError(f"Notification template with code '{code}' was not found.") from e

    @staticmethod
    def validate_template(template: NotificationTemplate) -> None:
        """
        Validates the state of a template (e.g., checks if active).

        Args:
            template (NotificationTemplate): The template to validate.

        Raises:
            TemplateServiceError: If the template is inactive or invalid.
        """
        if not template:
            raise TemplateServiceError("Template object is None.")

        if not template.is_active:
            raise TemplateServiceError(f"Template with code '{template.code}' is inactive.")

    @classmethod
    def invalidate_cache(cls, template_code: str) -> None:
        """Invalidate any cached template state. The current implementation is a no-op."""
        return None

    @classmethod
    def render_template(cls, body: str, variables: Dict[str, Any]) -> str:
        """
        Replaces placeholders in format '{variable_name}' with values from variables dictionary.
        Supports unlimited placeholders and enforces presence of all placeholders in variables.

        Args:
            body (str): The raw template string containing placeholders.
            variables (Dict[str, Any]): Dictionary of substitution values.

        Returns:
            str: The rendered template string.

        Raises:
            TemplateRenderingError: If a required placeholder is missing from the variables.
        """
        if not body:
            return ""

        # Find all placeholders matching {placeholder_name}
        placeholders = re.findall(r"\{([a-zA-Z0-9_]+)\}", body)
        rendered_body = body

        for placeholder in placeholders:
            if placeholder not in variables:
                raise TemplateRenderingError(
                    f"Template rendering failed: placeholder '{placeholder}' is required but was not provided in context variables."
                )
            
            value = variables[placeholder]
            rendered_body = rendered_body.replace(f"{{{placeholder}}}", str(value))

        return rendered_body
