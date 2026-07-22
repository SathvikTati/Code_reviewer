# Secret Management and Authentication

## Secret Management
Never hard-code secrets (passwords, API keys, tokens, private keys) in source code. Load them from environment variables or a secrets manager. Keep `.env` files out of version control via `.gitignore`. Do not log secrets. Rotate credentials that have been exposed. Detect accidental commits with secret-scanning tools.

## Password Handling
Never store passwords in plaintext or with fast/general-purpose hashes (MD5, SHA-1, SHA-256 alone). Use a slow, salted password hashing algorithm designed for the purpose: bcrypt, scrypt, or Argon2 (e.g. via `passlib` or `argon2-cffi`). Always use a unique random salt per password. Compare secrets using constant-time comparison (`hmac.compare_digest`) to avoid timing attacks.

## Authentication
Enforce strong authentication on every protected endpoint. Do not roll your own crypto or token schemes; use vetted libraries. For session tokens and JWTs, verify the signature, expiration, issuer, and audience. Set short expirations and support revocation. Rate-limit and lock out after repeated failed login attempts to slow brute force.

## Authorization
Check authorization on the server for every request, at the object level (does *this* user own *this* resource?). Do not rely on the UI hiding actions. Default to deny. Avoid insecure direct object references by validating ownership rather than trusting IDs from the client.

## Transport and Randomness
Use TLS for all traffic carrying credentials or sensitive data. Use the `secrets` module (not `random`) to generate tokens, salts, and password-reset codes, since `random` is not cryptographically secure.
