import pytest

from app.core.security import hash_password, password_needs_rehash, verify_password


def test_argon2id_password_hashing() -> None:
    password = "FactoryPilot#2026!"
    password_hash = hash_password(password)

    assert password_hash.startswith("$argon2id$")
    assert verify_password(password, password_hash) is True
    assert verify_password("WrongPassword#2026!", password_hash) is False
    assert password_needs_rehash(password_hash) is False


def test_password_strength_rejects_weak_password() -> None:
    with pytest.raises(ValueError, match="between 12 and 128"):
        hash_password("Short#1")
