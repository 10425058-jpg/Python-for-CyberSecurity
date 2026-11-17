# Deep Dive 10 — Python web APIs, authentication, authorization and injection defenses

**Level:** intermediate · **Estimated study:** 12–16 hours.

## Case study: a security report API

Users log in and request reports. The API must return a report only when the caller is authorized for that **specific report**, not merely authenticated. We will design this with pure Python examples to avoid relying on framework magic.

## 1. HTTP, state and trust boundaries

A client controls the URL, query parameters, headers and body. Proxies may add headers, but only explicitly trusted proxy infrastructure should influence security context. An application should not accept an arbitrary client-supplied `X-User-Id` as authenticated identity.

- **Authentication:** who is the caller?
- **Authorization:** may that caller read *this* report?
- **Session management:** how is caller identity maintained between requests?
- **Transport security:** how are requests protected in transit?
- **Audit:** can the server explain who accessed what and why?

These are separate design responsibilities.

## 2. Broken object-level authorization (IDOR/BOLA)

Suppose `GET /reports/101` reads a database row. If it checks only that a user is logged in, any logged-in user may change the numeric ID to view someone else's report.

### Reference policy

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class User:
    user_id: str
    roles: frozenset[str]

@dataclass(frozen=True)
class Report:
    report_id: str
    owner_id: str
    classification: str

def can_read_report(caller: User, report: Report) -> bool:
    # Example organization policy; real scopes may be more complex.
    if report.owner_id == caller.user_id:
        return True
    if "auditor" in caller.roles and report.classification == "organization":
        return True
    return False

alice = User("alice", frozenset({"reader"}))
bob = User("bob", frozenset({"reader"}))
report = Report("R-101", "alice", "personal")
assert can_read_report(alice, report)
assert not can_read_report(bob, report)
```

The server must derive `caller` from validated authentication state, not from a user-controlled request body. Authorize every read/write, including nested objects, bulk exports, background jobs and URLs for attachments.

## 3. Authentication and session handling

Strong authentication often uses password KDF storage, rate limits, MFA, secure recovery flows and protection from credential stuffing. For cookies: `Secure`, `HttpOnly`, appropriate `SameSite`, session rotation and expiry. For bearer tokens: strict signature/claims verification, audience, issuer, expiration and token type checks.

### JWT pitfalls
A JWT is usually three base64url-encoded segments, but **decoding the segments is not verification**. A verified JWT requires the accepted signature algorithm, key lookup trust, issuer, audience, clock checks and appropriate scopes. Avoid accepting whatever algorithm or key URL the incoming token requests.

### OAuth/OIDC
OAuth is a delegation framework; OpenID Connect adds identity semantics. Access tokens are for resource authorization, ID tokens for client identity context; do not swap them. Client-specific flows, state, PKCE and redirect URI validation must follow provider guidance.

## 4. SQL injection: data cannot become syntax

```python
# Dangerous (DO NOT USE):
# query = "SELECT * FROM reports WHERE owner_id = '" + user_id + "'"

# Safe:
cursor.execute(
    "SELECT report_id, owner_id, classification "
    "FROM reports WHERE report_id = ?",
    (requested_id,),
)
```

Parameterized SQL solves *value* injection, not object authorization. After finding a row, still run a correct access policy. Dynamic SQL identifiers need allowlists.

## 5. Template/HTML injection and XSS

Never insert raw user-controlled values into HTML, JavaScript, CSS or URL contexts. Use a templating framework with appropriate contextual escaping; escaping for one context may be unsafe in another. Avoid `Markup(...user_input...)`, disabling autoescape, or constructing script blocks with untrusted text. Content Security Policy (CSP) is defense in depth, not a replacement for correct encoding.

A security dashboard that prints attacker-controlled log messages without encoding can become an XSS carrier. Treat log data as adversarial: a malicious actor may intentionally write code-looking strings into login names or HTTP headers.

## 6. CSRF and CORS

**CSRF:** if a browser automatically attaches cookies, another site may be able to trigger state-changing requests. Mitigations include synchronizer/double-submit tokens as appropriate, SameSite, origin/referrer checks where applicable and avoiding unsafe state changes via GET.

**CORS:** controls which origins' browser JavaScript may read responses; it is **not** an API authentication mechanism, and server-to-server clients do not rely on it for authorization.

## 7. SSRF: the server as an unintended network client

If your API accepts any user-supplied URL and fetches it, an attacker may ask the server to contact internal services or cloud metadata. Defenses require:
- Prefer non-user-controlled, explicitly configured endpoints.
- Enforce accepted schemes/ports and strict identity/destination policies.
- Resolve and validate all destination addresses, including IPv6.
- Handle DNS rebinding and redirects; validate the actual connection destination.
- Network-level egress restrictions and metadata service protection.
- Response limits, rate limits, logging and monitored exceptions.

A regex that blocks `localhost` does not prevent all loopback or private-network addresses.

## 8. Filesystem and upload safety

A filename from a request must not determine an arbitrary write path. Generate server-side opaque IDs, store files outside executable/static roots, constrain permissions, enforce upload length and content policy, and inspect archives for traversal and decompression bombs. "Extension is .pdf" is not a content-verification guarantee.

## 9. API error handling and logging

- 400 for malformed request structure.
- 401 for missing/invalid authentication.
- 403 (or sometimes conceal existence with 404) when authorization is denied.
- 429 when rate limits apply.
- 5xx for internal failure, with a generic response and protected server-side diagnosis.

Never echo secrets, raw bearer tokens, database connection strings or entire user payloads in client errors. Logging should record enough for investigations without becoming a new privacy breach. Follow OWASP Logging Cheat Sheet.

## 10. Complete pure-Python service boundary example

```python
def lookup_report(requested_id: object, caller: User, database: dict[str, Report]):
    if not isinstance(requested_id, str) or not 1 <= len(requested_id) <= 64:
        raise ValueError("invalid report identifier")
    report = database.get(requested_id)
    if report is None:
        raise KeyError("not found")
    if not can_read_report(caller, report):
        raise PermissionError("access denied")
    return report

db = {"R-101": Report("R-101", "alice", "personal")}
assert lookup_report("R-101", alice, db).owner_id == "alice"
try:
    lookup_report("R-101", bob, db)
except PermissionError:
    pass
else:
    raise AssertionError("cross-user access was allowed")
```

This is domain logic, not a complete HTTP service. A real framework must validate the authenticated user, configure secure sessions, enforce request and output limits, and send appropriate status codes.

## 11. Hands-on exercises with answer checks

**A:** Add a `delete_report` operation. A report owner may delete; an auditor may read organization reports but may **not** delete. Test both roles and report classes.

**B:** Demonstrate a SQL statement that uses placeholders and retains an injection-shaped string as plain data. Verify a string like `"alice' OR 1=1 --"` returns no unauthorized rows.

**C:** Draw client → reverse proxy → app → DB trust boundaries. Label where authentication and authorization are enforced.

**D:** Write five negative API tests: wrong field type, missing authentication, other user's report, expired token and a forged client identity header. Document expected 400/401/403 outcomes.

**E:** Explain in two paragraphs why a TLS certificate and HTTP CORS configuration cannot substitute for a per-resource authorization check.

## 12. Framework-specific checklist

For Django/Flask/FastAPI (check current framework docs):
- Authentication and session settings correctly configured.
- Every object/query scoped to the principal.
- Input schemas and data size limits.
- Safe templating and response serialization.
- CSRF as appropriate for cookie sessions.
- File upload restrictions and storage isolation.
- Reverse proxy trusted headers correctly restricted.
- HTTPS settings, cookie attributes and HSTS when appropriate.
- Database roles minimally privileged.
- Debug mode off in deployment; no secrets in errors.
- CI and dependency review covering auth/security fixes.

**References:** [OWASP Authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html), [OWASP Authentication](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html), [OWASP SSRF](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html).
