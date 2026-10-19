# Scope and policy

## In scope

- Prompt-injection detection
- Email, phone, student-ID, and payment-card handling
- Sensitive-topic classification
- Public knowledge-base retrieval
- Structured model output
- Schema, groundedness, and leakage checks
- One corrective schema retry
- JSON-lines decision logging
- Deterministic evaluation and optional Gemini execution

## Out of scope

This assignment prototype does not provide authentication, admissions
decision-making, real student-record processing, payment processing, semantic
entailment, multilingual coverage, multi-turn attack state, or production
monitoring.

## Policy table

| Condition | Decision | Model call? | Action |
|---|---|---:|---|
| Prompt injection | Refuse | No | Safe refusal |
| Self-harm | Supportive response | No | Point to counseling resources |
| Payment-card number | Block | No | Safe fallback |
| Other PII | Continue | Yes | Mask typed placeholders |
| Medical topic | Decline | No | Redirect to a professional |
| Legal/visa topic | Continue with disclaimer | Yes | General policy information |
| Financial hardship | Continue with pointer | Yes | Financial-aid office |
| Invalid schema | Regenerate once | Maybe | Include validation feedback |
| Unsupported claim | Remove/fallback | No additional call | Keep supported content |
| Output PII | Continue after redaction | No additional call | Redact detected values |
| Confidential leak | Block | No | Safe fallback |
