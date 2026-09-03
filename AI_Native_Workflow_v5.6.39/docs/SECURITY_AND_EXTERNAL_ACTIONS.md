# Security and external-action guardrails

The workflow is a control/audit layer, not a sandbox or security boundary. Keep credentials out of model-visible files where possible; grant least privilege; isolate untrusted repositories and tools; validate external inputs; preserve immutable logs; and require human confirmation for destructive actions, submissions/releases, paid compute, credentials/private systems, privacy-sensitive operations, or other high-impact effects.

Prompt injection or malicious evidence can invalidate DIC assumptions. Environment-grounded verification, allowlisted tools, versioned dependencies, and independent release review remain necessary. A passing workflow state must never be interpreted as a security certification.
