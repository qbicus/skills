# Security Rules

- Never generate or store real secrets in repository files.
- Use placeholders for connection strings, API keys, passwords, tokens, and private keys.
- Avoid logging secrets, credentials, tokens, private keys, or full personal data.
- For auth, crypto, permissions, or data exposure changes, explain the risk and verification plan.
- Prefer least-privilege access.
- Do not weaken validation or authorization to make tests pass.
