from article_machine.standards import route_standards


def test_systematic_review_routes_to_required_guidelines() -> None:
    routed = route_standards("systematic-review")

    assert "PRISMA" in routed["guidelines"]
    assert "GRADE" in routed["guidelines"]
    assert "ROBIS" in routed["guidelines"]
    assert "AMSTAR 2" in routed["guidelines"]
    assert "RoB 2" in routed["risk_of_bias_tools"]
    assert "ROBINS-I" in routed["risk_of_bias_tools"]


def test_diagnostic_study_routes_to_stard_and_quadas() -> None:
    routed = route_standards("diagnostic-study")

    assert routed["guidelines"] == ["STARD 2015", "QUADAS-3"]


def test_drug_discovery_is_hypothesis_generating() -> None:
    routed = route_standards("drug-discovery")

    assert routed["lane"] == "computational-discovery"
    assert "hypothesis-generating" in routed["policy_labels"]
    assert "non-clinical" in routed["policy_labels"]
