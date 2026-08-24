# Authentication middleware stub

def require_auth(request):
    """Validate bearer token from Authorization header."""
    token = (request.headers.get('Authorization') or '').replace('Bearer ', '')
    if not token:
        raise Exception('Missing authorization token')
    # TODO: validate JWT
    return token
