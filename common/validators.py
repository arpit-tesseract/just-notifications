import re
from datetime import date, datetime
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_dob(value):
    """
    Validator to ensure Date of Birth is not in the future.
    """
    today = date.today()
    if isinstance(value, datetime):
        value = value.date()
    if value > today:
        raise ValidationError(_('Date of Birth cannot be in the future.'))
    return value

def validate_expired_date(value):
    """
    Validator to ensure Expired Date (Date of Death) is not in the future.
    """
    today = date.today()
    if isinstance(value, datetime):
        value = value.date()
    if value > today:
        raise ValidationError(_('Expired date (Date of Death) cannot be in the future.'))
    return value

def validate_marriage_date(value):
    """
    Validator to ensure Marriage Date is not in the future.
    """
    today = date.today()
    if isinstance(value, datetime):
        value = value.date()
    if value > today:
        raise ValidationError(_('Marriage date cannot be in the future.'))
    return value


def validate_email_format(value):
    """
    Validator to check if email format is valid using a standard regex.
    """
    email_regex = re.compile(
        r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    )
    if not email_regex.match(value):
        raise ValidationError(_('Enter a valid email address.'))
    return value


def validate_letters_only(value):
    """
    Validator to ensure the string contains only letters (no numbers or special characters).
    Useful for first name, last name, etc.
    """
    if not re.match(r'^[a-zA-Z\s]*$', value):
        raise ValidationError(_('This field must contain only letters and spaces.'))
    return value


def validate_alphanumeric(value):
    """
    Validator to ensure the string contains only letters and numbers.
    Useful for usernames, codes, etc.
    """
    if not re.match(r'^[a-zA-Z0-9]*$', value):
        raise ValidationError(_('This field must contain only alphanumeric characters.'))
    return value


def validate_password_strength(value):
    """
    Validator to check if password is strong enough.
    (At least 8 characters, at least one uppercase, one lowercase, one number)
    """
    if len(value) < 8:
        raise ValidationError(_('Password must be at least 8 characters long.'))
    if not any(char.isdigit() for char in value):
        raise ValidationError(_('Password must contain at least one digit.'))
    if not any(char.isupper() for char in value):
        raise ValidationError(_('Password must contain at least one uppercase letter.'))
    if not any(char.islower() for char in value):
        raise ValidationError(_('Password must contain at least one lowercase letter.'))
    return value


def validate_file_size(value):
    """
    Validator to limit uploaded file sizes to e.g. 5MB.
    Assumes value is a Django UploadedFile.
    """
    limit = 5 * 1024 * 1024 # 5 MB
    if value.size > limit:
        raise ValidationError(_('File too large. Size should not exceed 5 MB.'))
    return value

def validate_gstin(value):
    """
    Validator to ensure correct 15-character Indian GSTIN format.
    """
    gstin_regex = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    if not re.match(gstin_regex, str(value).upper()):
        raise ValidationError(_('Enter a valid 15-character GSTIN.'))
    return value.upper()
