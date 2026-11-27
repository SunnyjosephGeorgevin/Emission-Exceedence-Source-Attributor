from src.agents.inspection_planner import InspectionPlanner


def test_priority_score():

    planner = InspectionPlanner(max_distance_km=20)

    candidate = {
        "distance_km": 5,
        "is_directionally_aligned": True,
    }

    score = planner.calculate_score(candidate)

    assert score == 90.0


def test_unaligned_candidate_score():

    planner = InspectionPlanner(max_distance_km=20)

    candidate = {
        "distance_km": 10,
        "is_directionally_aligned": False,
    }

    score = planner.calculate_score(candidate)

    assert score == 20.0


def test_no_exceedance_returns_empty_plan():

    planner = InspectionPlanner()

    result = planner.generate_plan(
        exceedance_result={
            "is_exceedance": False,
            "station_id": "ST-001",
            "exceedance_count": 0,
            "exceedances": [],
        },
        candidates=[],
        facility_profiles=[],
    )

    assert result["status"] == "no_exceedance"
    assert result["recommendations"] == []