def require_auth(request):
    token = (request.headers.get('Authorization') or '').replace('Bearer ', '')
    if not token:
        raise Exception('Missing authorization token')
    # TODO: validate JWT
    return token
