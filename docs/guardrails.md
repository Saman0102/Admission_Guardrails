# Guardrails

## Input guardrails

| Guardrail | Detection | Action when flagged | Limitation |
|---|---|---|---|
| Prompt injection | Unicode normalization and weighted regex patterns | Refuse before model call | Misses novel, encoded, multilingual, and multi-turn paraphrases |
| PII | Email, phone, fictional student ID, and Luhn-valid card patterns | Mask ordinary PII; block payment cards | Does not cover every name, address, or obfuscated format |
| Sensitive topics | Ordered keyword categories | Self-harm/medical refusal; legal disclaimer; financial-aid pointer | Keywords are context-sensitive and can miss indirect wording |

Input order is intentional: injection is checked first so likely instruction
overrides never reach the model; ordinary PII is then masked; topic policy is
applied to the cleaned text.

## Output guardrails

| Guardrail | Detection | Action when flagged | Limitation |
|---|---|---|---|
| Schema | JSON parse, required fields, types, enums, source IDs, bounds | Retry once with validation feedback, then fallback | A valid shape can still contain a misleading claim |
| Groundedness | Sentence-level lexical overlap, numbers, and negation checks | Keep supported claims or return fallback | Not semantic entailment; paraphrase remains difficult |
| Sensitive information | Known confidential KB strings, prompt fragments, and PII patterns | Redact ordinary PII; fallback for confidential/system leakage | Cannot guarantee detection of unseen paraphrases |

## Response policy

Every successful response is structured with:

```json
{
  "answer": "string",
  "sources": ["KB003"],
  "confidence": 0.85,
  "category": "fees",
  "status": "answered"
}
```

The system is an assignment prototype, not an admissions decision system. It
must only use fictional data and should have human review for sensitive cases.
