# Trustworthy Admissions FAQ Assistant — Report

## Summary

This project implements a fictional admissions FAQ assistant with defense-in-
depth input and output guardrails. It uses public-only retrieval, structured
responses, a deterministic mock provider for reproducible tests, and an
optional Google AI Studio Gemini provider.

## Design

The pipeline is:

```text
input → injection → PII → sensitive topic → public retrieval → model
      → schema → groundedness → sensitive-information check → response
```

See [architecture.md](architecture.md) and [guardrails.md](guardrails.md) for
component details and decisions.

## Results

The authored suite contains 35 cases. After the groundedness improvement,
status pass rate is `0.885714` and action pass rate is `0.800000`. Groundedness
precision improved from `0.333` to `0.667`, and recall improved from `0.250` to
`1.000`.

See [evaluation.md](evaluation.md) and [comparison.md](comparison.md).

## Trade-offs

Masking ordinary PII instead of rejecting every request preserves usability,
but residual risk remains for formats the detector does not recognize. Blocking
payment cards is stricter because disclosure has higher consequences. A stricter
groundedness threshold can reduce unsupported answers but may reject legitimate
paraphrases. The system therefore uses explainable thresholds and records the
trade-off rather than claiming perfect safety.

## Limitations and risks

Pattern-based injection and PII detection can miss obfuscation, paraphrases,
other languages, and unseen formats. Lexical groundedness is not semantic
entailment. The evaluation is small, deterministic, and single-turn.

Remaining risks include adaptive prompt injection, confidential information
paraphrased by a model, incorrect retrieval, stale knowledge-base facts,
provider outages, and unsafe use with real student records. Gemini execution
adds network, quota, cost, and provider-retention considerations.

## Evaluation and verification

```powershell
python -m pytest tests -q
python run_evaluation.py
python run_after_fix.py
python run_tradeoff.py
```

The automated suite contains 20 tests. The authored evaluation suite contains
35 cases, and each generated result records expected and actual status/action
values.
