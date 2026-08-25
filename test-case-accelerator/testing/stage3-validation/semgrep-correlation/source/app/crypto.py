import hashlib


class TokenHasher:
    def digest(self, token: str) -> str:
        return hashlib.md5(token.encode()).hexdigest()
