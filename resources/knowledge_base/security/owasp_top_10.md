# OWASP Top 10 (2021) for Python

## A01: Broken Access Control
Enforce authorization on the server for every request and at the object level:
verify the current user may act on the specific resource, not just that they are
logged in. Deny by default. Do not rely on hidden UI or client-supplied role
flags. Avoid insecure direct object references (IDOR) by checking ownership
rather than trusting IDs from the request.

## A02: Cryptographic Failures
Protect sensitive data in transit (TLS) and at rest. Never invent crypto. Use
vetted libraries and modern algorithms; avoid MD5/SHA-1 for security. Hash
passwords with bcrypt/scrypt/Argon2 and a unique salt. Generate tokens and salts
with the `secrets` module, never `random`. Do not log secrets or PII.

## A03: Injection
Never build SQL, shell, or query strings from untrusted input. Use parameterized
queries / the ORM's binding API; avoid `subprocess(..., shell=True)` and pass
argument lists. Validate and encode based on the sink. Avoid `eval`, `exec`, and
unsafe deserialization (`pickle`, `yaml.load`).

## A04: Insecure Design
Threat-model features before building. Apply least privilege, defense in depth,
secure defaults, and fail-secure error handling. Rate-limit sensitive endpoints.
Security is a design property, not a bolt-on.

## A05: Security Misconfiguration
Ship secure defaults: disable debug in production, remove default credentials,
restrict CORS, set security headers, and keep configuration and secrets out of
source (use environment/secret managers). Do not expose stack traces to users.

## A06: Vulnerable and Outdated Components
Track dependencies, pin versions, and scan for known CVEs (e.g. `pip-audit`).
Remove unused packages. Update promptly when advisories are published.

## A07: Identification and Authentication Failures
Use strong, vetted authentication. Enforce lockout/rate limiting on login,
secure session/token handling (verify signature, expiry, issuer/audience for
JWTs), and support revocation. Never store or transmit passwords in plaintext.

## A08: Software and Data Integrity Failures
Verify integrity of updates, plugins, and CI/CD artifacts. Do not deserialize
untrusted data. Pin and verify dependency hashes for reproducible, tamper-evident
builds.

## A09: Security Logging and Monitoring Failures
Log authentication, authorization, and input-validation failures with enough
context to investigate — without logging secrets or full PII. Ensure logs are
monitored and tamper-resistant.

## A10: Server-Side Request Forgery (SSRF)
When making outbound requests from user-supplied URLs, validate the host against
an allow-list, block internal/link-local ranges, and disable following redirects
to untrusted hosts.
