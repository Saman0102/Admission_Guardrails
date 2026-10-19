# Evaluation

The authored evaluation suite contains 35 cases covering normal questions,
PII, prompt injection, sensitive topics, schema failures, groundedness, and
output leakage. Expected outcomes are written before execution in
[`data/test_cases.json`](../data/test_cases.json).

Run it with:

```powershell
python run_evaluation.py
```

The generated records are stored in [`results/`](../results/).

## Current after-fix metrics

| Guardrail | TP | FP | TN | FN | Precision | Recall |
|---|---:|---:|---:|---:|---:|---:|
| Injection | 4 | 0 | 28 | 3 | 1.000 | 0.571 |
| PII | 4 | 1 | 29 | 1 | 0.800 | 0.800 |
| Sensitive topic | 4 | 0 | 31 | 0 | 1.000 | 1.000 |
| Groundedness | 4 | 2 | 29 | 0 | 0.667 | 1.000 |
| Output leakage | 2 | 0 | 33 | 0 | 1.000 | 1.000 |

Overall status pass rate is `0.885714`; action pass rate is `0.800000`.

## Test and artifact commands

```powershell
python -m pytest tests -q
python run_evaluation.py
python run_after_fix.py
python run_tradeoff.py
```

The test suite verifies the guardrail modules and evaluation assets. The
evaluation runner verifies labeled behavior and produces confusion-matrix
metrics, while the trade-off runner measures a stricter groundedness threshold.

## Known failures

- Obfuscated email such as `name at example dot edu` can be missed.
- Some injection paraphrases are not detected.
- The detector is not a semantic groundedness or entailment model.
- Groundedness false positives can occur when a leakage response contains
  claims outside its cited public source.
