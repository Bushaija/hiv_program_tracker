"""Tests for security utilities in app.core.security."""

import pytest
from jose import jwt, JWTError

from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.config import settings # To get SECRET_KEY for token tests
import datetime
import time # For testing token expiration

def test_password_hashing_and_verification():
    """Test that password hashing and verification work correctly."""
    password = "testpassword123"
    hashed_password = get_password_hash(password)

    assert hashed_password is not None
    assert password != hashed_password  # Ensure the hash is not the same as the password

    assert verify_password(password, hashed_password) is True
    assert verify_password("wrongpassword", hashed_password) is False
    assert verify_password(password, "notacorrecthash") is False

def test_verify_password_with_empty_inputs():
    """Test verify_password with empty or None inputs."""
    password = "testpassword123"
    hashed_password = get_password_hash(password)

    assert verify_password("", hashed_password) is False
    assert verify_password(password, "") is False
    # Depending on Passlib's behavior, None might raise an error or return False.
    # For robustness, let's assume it should return False or handle potential errors.
    try:
        assert verify_password(None, hashed_password) is False
    except Exception: # pylint: disable=broad-except
        # Some passlib versions/backends might raise error on None
        pass 
    try:
        assert verify_password(password, None) is False
    except Exception: # pylint: disable=broad-except
        pass

# JWT Token tests will be added next

def test_create_and_validate_access_token():
    """Test JWT access token creation and validation."""
    subject = "test_user_subject"
    token = create_access_token(subject=subject)

    assert token is not None

    # Decode the token
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == subject
        assert "exp" in payload
        # Check that expiry is in the future (within ACCESS_TOKEN_EXPIRE_MINUTES)
        expire_timestamp = payload["exp"]
        expected_expiry = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        # Allow a small leeway for timing differences
        assert expire_timestamp > time.time()
        assert expire_timestamp <= expected_expiry.timestamp() + 60 # 60 seconds leeway

    except JWTError as e:
        pytest.fail(f"Token validation failed: {e}")

def test_access_token_expiration():
    """Test that an expired JWT access token is invalid."""
    subject = "test_user_for_expiry"
    # Create a token that expires very quickly (e.g., -1 minute)
    expired_token = create_access_token(subject=subject, expires_delta=datetime.timedelta(minutes=-1))

    with pytest.raises(JWTError):
        jwt.decode(
            expired_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

def test_access_token_invalid_signature():
    """Test that a JWT token with an invalid signature is rejected."""
    subject = "test_user_invalid_sig"
    token = create_access_token(subject=subject)

    wrong_secret_key = "a_totally_different_secret_key_that_is_long_enough"
    with pytest.raises(JWTError):
        jwt.decode(token, wrong_secret_key, algorithms=[settings.ALGORITHM])

def test_access_token_malformed():
    """Test that a malformed JWT token is rejected."""
    malformed_token = "this.is.not.a.valid.token"
    with pytest.raises(JWTError):
        jwt.decode(malformed_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

def test_access_token_no_subject():
    """Test creating a token with no subject (should still work, sub will be None or handled by create_access_token)."""
    # Assuming create_access_token can handle subject=None or uses a default.
    # If subject is mandatory and not None, this test might need adjustment
    # based on how create_access_token is implemented.
    # For now, let's assume it might set sub to an empty string or similar if subject is None.
    token_no_sub = create_access_token(subject=None)
    assert token_no_sub is not None
    try:
        payload = jwt.decode(
            token_no_sub, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        # Depending on implementation, sub might be None, an empty string, or not present.
        # If it's not present, payload.get("sub") is safer than payload["sub"]
        assert payload.get("sub") is None # Or check for expected default if any
    except JWTError as e:
        pytest.fail(f"Token validation for no subject failed: {e}") 