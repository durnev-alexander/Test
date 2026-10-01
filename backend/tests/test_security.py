from app.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_is_not_plain_text_and_verifies():
    hashed = hash_password("demo")
    assert hashed != "demo"
    assert verify_password("demo", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_round_trip():
    token = create_access_token("demo")
    payload = decode_access_token(token)
    assert payload["sub"] == "demo"
    assert "exp" in payload
