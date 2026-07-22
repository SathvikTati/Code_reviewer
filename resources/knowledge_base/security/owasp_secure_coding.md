# OWASP Secure Coding Practices (Python)

## Input Validation
Validate all input on the server side. Treat every value coming from the network, files, environment, or a database as untrusted. Prefer allow-lists (accept known-good) over deny-lists. Validate type, length, format, and range before use. Reject invalid input rather than trying to sanitize it into something usable.

## Injection Prevention
Never build SQL, shell commands, or queries by concatenating user input. Use parameterized queries / prepared statements (e.g. cursor.execute("... WHERE id = %s", (user_id,))). For OS commands, avoid `os.system` and `subprocess` with `shell=True`; pass argument lists instead. For NoSQL and ORMs, use the driver's binding API rather than string interpolation.

## Output Encoding
Encode data on output according to the sink (HTML, URL, JSON, shell). In web templates, rely on the framework's auto-escaping and never mark untrusted data as "safe". Set the correct Content-Type so browsers do not sniff.

## Deserialization
Never `pickle.loads` or `yaml.load` untrusted data — both allow arbitrary code execution. Use `yaml.safe_load` and `json` for untrusted input. Avoid `eval`, `exec`, and `__import__` on any value derived from user input.

## Error Handling and Logging
Fail securely: on error, deny access rather than granting it. Do not leak stack traces, secrets, SQL, or internal paths to end users. Log security-relevant events (authentication, authorization failures, input validation failures) without logging secrets or full PII.

## Path Traversal / SSRF
When opening files from user-supplied names, resolve the path and confirm it stays inside an allowed base directory. For outbound requests built from user input, validate the host against an allow-list to prevent server-side request forgery.
