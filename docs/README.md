# Admissions Guardrails Documentation

This folder contains the design, operation, evaluation, and comparison
documentation for the fictional admissions FAQ assistant.

## Documentation map

- [Setup](setup.md) — install dependencies, configure Gemini, run the UI and tests.
- [Architecture](architecture.md) — components and request flow.
- [Guardrails](guardrails.md) — each input/output control, action, and limitation.
- [Evaluation](evaluation.md) — authored test suite, metrics, and failure analysis.
- [Before and after comparison](comparison.md) — unguarded versus guarded behavior
  and measured baseline versus after-fix results.
- [Assignment report](report.md) — concise design, results, trade-offs, and risk verdict.
- [Scope and policy](scope.md) — in-scope behavior and fail-closed policy table.
- [Input guardrails](input_guardrails.md) — input detection details.
- [Output guardrails](output_guardrails.md) — output validation details.

The authoritative case definitions are in
[`data/test_cases.json`](../data/test_cases.json). Generated evaluation artifacts
are in [`results/`](../results/).
