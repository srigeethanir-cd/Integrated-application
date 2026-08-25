# Expected Stage 3 Results

- Five `/api/auth` endpoints: register, login, refresh, me and admin.
- Dependencies: `get_db`, `OAuth2PasswordRequestForm`, `oauth2_scheme`, `get_current_user`, `require_admin`.
- Models `User` and `RefreshToken`, foreign key and cascade relationship.
- PBKDF2 password hashing and HMAC-signed access/refresh tokens.
- Custom credential/token errors and HTTP 401, 403 and 409 mappings.
