def authenticate_user(email: str, password: str):
    if email and len(password) >= 8:
        return f"mock_jwt_token_for_{email}"
    return None
