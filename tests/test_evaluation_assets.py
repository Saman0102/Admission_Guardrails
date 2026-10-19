import json


def test_authored_suite_has_required_size_and_groups():
    with open("data/test_cases.json", encoding="utf-8") as handle:
        cases = json.load(handle)
    assert len(cases) >= 25
    assert {"normal", "pii", "injection", "sensitive", "schema", "groundedness", "leakage"} <= {
        case["group"] for case in cases
    }
    assert all("ground_truth" in case for case in cases)


def test_expected_outcomes_are_present_before_runner_output():
    with open("data/test_cases.json", encoding="utf-8") as handle:
        cases = json.load(handle)
    assert all(case["expected_status"] in {"answered", "refused", "fallback"} for case in cases)
    assert all(case["expected_action"] for case in cases)
