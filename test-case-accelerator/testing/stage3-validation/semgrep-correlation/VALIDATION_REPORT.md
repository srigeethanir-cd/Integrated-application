# Semgrep Correlation Validation Report

Date: 2026-07-31

## Scope

This validation exercises the installed Semgrep runner, the security finding
normalizer, and the deterministic Stage 3 analyzer. It verifies correlation
only; it does not assess the coverage of external Semgrep registry rulesets.

The repository contains one intentional instance of each requested category:

- SQL injection
- Hardcoded secret
- Dangerous subprocess execution
- `eval()`
- Weak cryptography

The local ruleset makes the run reproducible without Semgrep registry access.

## Result

Overall status: **PASS**

| Finding | File | Function | Class | Endpoint | Result |
| --- | --- | --- | --- | --- | --- |
| SQL injection | `app/api.py` | `unsafe_user_lookup` | None | `GET /tools/users` | PASS |
| Hardcoded secret | `app/secrets.py` | `load_partner_credentials` | None | None | PASS |
| Dangerous subprocess | `app/commands.py` | `execute` | `CommandRunner` | None | PASS |
| `eval()` | `app/api.py` | `evaluate_expression` | None | `POST /tools/evaluate` | PASS |
| Weak cryptography | `app/crypto.py` | `digest` | `TokenHasher` | None | PASS |

## Accuracy

- Semgrep findings preserved in Stage 3: **5/5 (100%)**
- Correct file correlation: **5/5 (100%)**
- Correct function correlation: **5/5 (100%)**
- Correct class correlation or non-correlation: **5/5 (100%)**
- Correct endpoint correlation or non-correlation: **5/5 (100%)**
- Missing attachments: **0**
- Incorrect attachments: **0**
- Duplicate attachments: **0**
- Stage 3 deterministic across two analyses: **PASS**

## Defect Assessment

No correlation defects were reproduced. The existing behavior correctly:

- retains every normalized Semgrep finding at the Stage 3 root;
- attaches findings to a function only when the finding line is inside it;
- attaches method findings to their containing class;
- propagates endpoint-function findings to the matching endpoint;
- avoids attaching ordinary function and class-method findings to endpoints.

No extraction logic was modified.

## Reproduction

From the backend directory, run:

```powershell
$env:DEBUG='false'
.\.venv\Scripts\python.exe ..\testing\stage3-validation\semgrep-correlation\validate.py
```

The script exits with status `0` only when all five correlations match the
expected file, function, class, and endpoint scopes and two Stage 3 outputs are
identical.
