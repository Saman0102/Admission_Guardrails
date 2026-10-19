# After-fix evaluation

Improvement: groundedness now checks numeric consistency and rejects claims with unsupported negation.

## Before and after

| Guardrail | Before precision | After precision | Before recall | After recall |
|---|---:|---:|---:|---:|
| injection | 1.0 | 1.0 | 0.5714285714285714 | 0.5714285714285714 |
| pii | 0.8 | 0.8 | 0.8 | 0.8 |
| sensitive_topic | 1.0 | 1.0 | 1.0 | 1.0 |
| groundedness | 0.3333333333333333 | 0.6666666666666666 | 0.25 | 1.0 |
| output_leakage | 1.0 | 1.0 | 1.0 | 1.0 |

- Status pass rate before: 0.8571428571428571
- Status pass rate after: 0.8857142857142857
- Action pass rate before: 0.7714285714285715
- Action pass rate after: 0.8
