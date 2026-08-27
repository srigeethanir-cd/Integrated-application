# Expected Stage 3 Results

- Routes: `POST /api/banking/accounts`, `GET /api/banking/accounts`, `POST /api/banking/transfers`.
- Models: `Account`, `Transaction`; foreign key `transactions.account_id`; bidirectional relationship.
- Dependencies: `get_db`, `authenticate`.
- Exceptions: HTTP 401, 404, 409; custom `InsufficientFundsError`.
- Session behavior: commit, refresh, rollback, close and `yield db`.
