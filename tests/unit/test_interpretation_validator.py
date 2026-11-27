
from src.agents.interpretation_validator import InterpretationValidator


def get_valid_interpretation():

    return {
        "ambient_analysis": (
            "PM25 measured 180 against threshold 100. "
            "PM10 measured 240 against threshold 150."
        ),
        "wind_analysis": (
            "Wind conditions were observed during the investigation."
        ),
        "facility_analysis": (
            "Alpha Cement Works is 1.55 km away "
            "with a screening score of 36.9."
        ),
        "limitations": [
            "All data is synthetic."
        ],
        "recommendations": [
            "Conduct further investigation and verify facility records."
        ],
    }


def get_sample_investigation():

    return {
        "exceedance_result": {
            "exceedances": [
                {
                    "pollutant": "pm25",
                    "measured_value": 180,
                    "threshold": 100,
                },
                {
                    "pollutant": "pm10",
                    "measured_value": 240,
                    "threshold": 150,
                },
            ]
        },
        "screened_candidates": [
            {
                "facility_name": "Alpha Cement Works",
                "distance_km": 1.55,
                "is_directionally_aligned": False,
            }
        ],
        "investigation_plan": {
            "recommendations": [
                {
                    "facility_name": "Alpha Cement Works",
                    "priority_score": 36.9,
                    "priority_level": "medium",
                }
            ]
        },
    }


def test_valid_interpretation():

    validator = InterpretationValidator()

    result = validator.validate(
        get_valid_interpretation(),
        get_sample_investigation(),
    )

    assert result["is_valid"] is True
    assert result["error_count"] == 0


def test_rejects_invented_units():

    validator = InterpretationValidator()

    interpretation = get_valid_interpretation()

    interpretation["ambient_analysis"] += (
        " Values are measured in ppm."
    )

    result = validator.validate(
        interpretation,
        get_sample_investigation(),
    )

    assert result["is_valid"] is False
    assert any(
        "unit" in error.lower()
        for error in result["errors"]
    )


def test_rejects_missing_measurements():

    validator = InterpretationValidator()

    interpretation = get_valid_interpretation()

    interpretation["ambient_analysis"] = (
        "Pollution measurements were elevated."
    )

    result = validator.validate(
        interpretation,
        get_sample_investigation(),
    )

    assert result["is_valid"] is False

    assert any(
        "measured value" in error.lower()
        for error in result["errors"]
    )


def test_missing_facility_distance_does_not_reject_interpretation():

    validator = InterpretationValidator()

    interpretation = get_valid_interpretation()

    interpretation["facility_analysis"] = (
        "Alpha Cement Works has a medium screening priority "
        "with score 36.9."
    )

    result = validator.validate(
        interpretation,
        get_sample_investigation(),
    )

    assert result["is_valid"] is True
    assert result["error_count"] == 0
