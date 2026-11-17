# Deep Dive 10 — Python web APIs, authentication, authorization and injection defenses

> **Hands-on:** [Chapter 10 Guided Lab](../lab-manual/10-GUIDED-LAB.md) · [100 worked answers](../solutions/by-exercise/README.md). Run negative tests and document limitations.

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


## 12. A complete resource-access decision: ownership, tenant and permission

When designing a security dashboard, checking "the user has role analyst" is not enough if the request targets a report belonging to a different organization. Broken object-level authorization (BOLA/IDOR) commonly appears when code validates identity but does not check the *specific target resource*.

### A minimal, testable authorization core

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Principal:
    subject: str
    tenant: str
    permissions: frozenset[str]

@dataclass(frozen=True)
class Report:
    report_id: str
    tenant: str
    owner: str
    classification: str

def may_read(p: Principal, item: Report) -> bool:
    if p.tenant != item.tenant:
        return False
    if item.owner == p.subject:
        return "report:read-own" in p.permissions
    return ("report:read-org" in p.permissions
            and item.classification == "organization")

alex = Principal("alex", "tenant-a", frozenset({"report:read-own"}))
sam = Principal("sam", "tenant-b", frozenset({"report:read-org"}))
r = Report("r-100", "tenant-a", "alex", "personal")
assert may_read(alex, r)
assert not may_read(sam, r)
```

**Critical boundary:** the `Principal` must come from a validated server-side authentication session/token, never from request parameters. The `Report` must come from a trusted repository that enforces the record's tenant and classification correctly; a client-supplied "tenant" is not authoritative.

### Decision table

| Caller | Tenant match? | Owns report? | Permissions | Decision |
|---|---|---|---|---|
| Alex | yes | yes | read-own | allow |
| Alex | yes | no | read-own | deny |
| Auditor | yes | no | read-org; org report | allow |
| Auditor | yes | no | read-org; personal report | deny |
| Cross-tenant admin | no | any | any | deny under this policy |

A production policy may require additional purpose-based access, approvals or legal restrictions. The example is intentionally strict across tenants.

## 13. SQL injection prevention is not authorization

Even a parameterized query like `SELECT * FROM reports WHERE id = ?` can return another user's row if the application fails to scope by tenant or check the returned object's ownership. Prefer enforcing multiple layers: parameterized values, query scope, authoritative object metadata, access decision, audit, and output redaction.

**Ordering example:**
1. Authenticate the caller.
2. Validate report ID format/length.
3. Read the requested report under a tenant-constrained query.
4. Evaluate resource-level permission on the result.
5. Serialize only fields the principal may see.
6. Audit the decision without copying secrets into logs.

## 14. Browser security: CSRF, CORS and cookies are different

- **Cookie-based authentication** often needs CSRF mitigations for state-changing requests because browsers can attach cookies automatically.
- **SameSite** can help but its exact behavior depends on deployment and browser context.
- **CORS** determines which origins' browser scripts may read cross-origin responses; it is not server-side authentication or authorization.
- **HttpOnly** reduces ordinary JavaScript access to cookies; it does not make an XSS vulnerability harmless.
- **Secure** restricts cookies to secure transport under supported browser behavior; correct HTTPS and session lifetime remain necessary.

### Threat model a "delete report" endpoint
Use POST/DELETE with correct session authentication, per-object authorization, CSRF defenses if cookie-based, an audit trail, safe retries and a confirmation workflow for highly impactful actions. Do not mutate state on a simple GET.

## 15. Input and output contexts

An authenticated internal log message may contain user-controlled text. Rendering it inside a browser without context-appropriate encoding can introduce XSS. A validated username may still contain characters significant in HTML. Conversely, HTML-escaping a string does not make it safe for SQL: **use the defense appropriate to the sink**.

| Sink | Defensive mechanism |
|---|---|
| SQL values | bound parameters |
| HTML text | HTML text-context escaping |
| HTML attributes | attribute-context escaping |
| Shell arguments | trusted executable + explicit argument validation; no shell strings |
| Filesystem | safe storage root, generated names, secure OS file operations |
| Server-side URL fetch | strict destination and egress rules |
| JSON response | JSON serializer, correct content type, client-side safe rendering |

## 16. Hands-on exercises

**A:** Add an `is_admin` flag to `Principal` and demonstrate why an admin flag must not bypass the tenant boundary by accident.

**B:** Create tests for read-own, read-org, denied cross-tenant and denied personal-report access.

**C:** Write an access-control matrix for GET/POST/DELETE and identify which server-side checks apply to every operation.

**D:** Design a redacted log entry for denied access. Include request ID, pseudonymous principal, resource ID and reason code; omit tokens, cookies and sensitive report content.

**E:** Explain why CORS `Access-Control-Allow-Origin: *` does not by itself enable a server-to-server client to obtain protected resources, and why it is still risky in certain browser-accessible contexts.

**F:** Contrast a valid token with an authorized request. An intact signature can prove token integrity while its audience/permissions may still be wrong.

**Further reading:** [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html), [OWASP Input Validation](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html).
