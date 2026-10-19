# Input guardrails

Input processing is ordered and fail-closed where the risk is high:

```text
validation → injection → PII → sensitive topic
```

## Prompt injection

`src/input_injection.py` normalizes text and applies categorized weighted
patterns for instruction overrides, prompt extraction, persona jailbreaks, and
restriction bypasses. A score at or above the configured threshold returns a
refusal before retrieval or model execution.

## PII

`src/pii_guardrail.py` detects email addresses, phone numbers, fictional
student IDs, and payment-card candidates. Ordinary PII is replaced with typed
placeholders such as `[EMAIL]`. Card candidates are checked with Luhn
validation and valid cards are blocked.

## Sensitive topics

`src/sensitive_topics.py` classifies self-harm, medical, legal/visa, and
financial-hardship requests. Each category has a distinct action rather than a
single generic block.

## Limitations

These controls are explainable regex/keyword rules. They can miss obfuscation,
paraphrases, other languages, names, addresses, and multi-turn attacks.
