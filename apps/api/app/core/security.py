from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from argon2.low_level import Type

_password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
    type=Type.ID,
)


def validate_password_strength(password: str) -> None:
    if not 12 <= len(password) <= 128:
        raise ValueError("Password must contain between 12 and 128 characters")
    if any(character.isspace() for character in password):
        raise ValueError("Password must not contain whitespace")
    if not any(character.islower() for character in password):
        raise ValueError("Password must contain a lowercase character")
    if not any(character.isupper() for character in password):
        raise ValueError("Password must contain an uppercase character")
    if not any(character.isdigit() for character in password):
        raise ValueError("Password must contain a digit")
    if not any(not character.isalnum() for character in password):
        raise ValueError("Password must contain a special character")


def hash_password(password: str) -> str:
    validate_password_strength(password)
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (InvalidHashError, VerificationError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    try:
        return _password_hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return True
