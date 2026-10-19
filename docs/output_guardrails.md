# Output guardrails

Output processing is ordered:

```text
schema → groundedness → sensitive-information detection
```

## Schema validation

The response must be valid JSON with required fields:

- `answer`
- `sources`
- `confidence`
- `category`
- `status`

Types, source IDs, confidence bounds, category/status enums, and answer length
are checked. Invalid output triggers one retry with specific validation
feedback. A second failure produces a schema-shaped fallback.

## Groundedness

`src/groundedness.py` checks sentence-level content overlap against cited public
knowledge-base entries. The improved version also checks numbers and simple
negation consistency. Unsupported claims are removed when enough supported
content remains; otherwise a safe fallback is returned.

## Sensitive information

`src/output_sensitive.py` checks output for ordinary PII, confidential
knowledge-base strings, and selected system-prompt fragments. Ordinary PII is
redacted. Confidential or system-prompt leakage returns a fallback.

## Limitations

Lexical overlap is not semantic entailment. The detector may miss paraphrased,
encoded, or previously unseen confidential information.
