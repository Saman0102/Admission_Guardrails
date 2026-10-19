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


def test_latest_results_record_expected_and_actual_outcomes():
    with open("results/latest.json", encoding="utf-8") as handle:
        report = json.load(handle)
    cases = report["cases"]
    assert len(cases) >= 20
    assert all("expected_status" in case for case in cases)
    assert all("actual_status" in case for case in cases)
    assert all("expected_action" in case for case in cases)
    assert all("actual_action" in case for case in cases)
