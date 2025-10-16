import re
from datetime import date
from django.core.exceptions import ValidationError

# def validate_contact_no(contact_no):
#     """
#     Validates that the contact number is in the format '+{code} {number}'.
#     - Country code: 1-4 digits.
#     - Number: 6-14 digits.
#     This check is independent of any database field length.
#     """
#     # accepted number example: "+91 8878765432"
#     pattern = r'^\+\d{1,4}\s\d{6,14}$'
#     if not re.match(pattern, contact_no):
#         return ValidationError("Please enter a valid contact number.")


def validate_email(email):
    pattern = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    if not re.match(pattern, email):
        return ValidationError("Please enter a valid email address.")


def validate_full_name(value):
    """
    Validates that the name:
    1. Contains exactly one space.
    2. The parts (first and last name) are longer than 2 characters.
    3. Contains only alphabetic characters.
    """
    # Check for exactly one space
    if value.count(' ') != 1:
        raise ValidationError("Please provide a first and last name separated by a single space.")

    # Split into two parts
    first_name, last_name = value.split(' ')

    # Check length of the first name
    if len(first_name) <= 2:
        raise ValidationError("The first name must be longer than 2 characters.")

    # Check length of the last name
    if len(last_name) <= 2:
        raise ValidationError("The last name must be longer than 2 characters.")

    # Check if both parts contain only letters
    if not first_name.isalpha() or not last_name.isalpha():
        raise ValidationError("Names can only contain letters.")

def validate_blood_group(value):
    """
    Validates that the blood group is one of the standard eight types.
    The check is case-insensitive.
    """
    # This allows the field to be optional (empty string or None)
    if not value:
        return

    valid_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    
    # Perform a case-insensitive check
    if value.upper() not in valid_groups:
        raise ValidationError(f"{value} is not a valid blood group. Please use one of: {valid_groups}")
    
def validate_dob(value):
    if value > date.today():
        raise ValidationError("Date of birth cannot be in the future.")