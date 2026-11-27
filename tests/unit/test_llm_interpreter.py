
import asyncio

from src.agents.llm_interpreter import LLMInterpreter
from src.data.models import LLMInterpretation


async def main():

    interpreter = LLMInterpreter()

    sample_result = {
        "status": "success",
        "station_id": "ST-001",
        "investigation_timestamp": "2026-11-25T10:00:00+00:00",

        "exceedance_result": {
            "is_exceedance": True,
            "exceedance_count": 3,
            "exceedances": [
                {
                    "pollutant": "pm25",
                    "measured_value": 180,
                    "threshold": 100,
                    "excess": 80,
                },
                {
                    "pollutant": "pm10",
                    "measured_value": 240,
                    "threshold": 150,
                    "excess": 90,
                },
                {
                    "pollutant": "nox",
                    "measured_value": 85,
                    "threshold": 80,
                    "excess": 5,
                },
            ],
        },

        "wind_reading": {
            "wind_speed": 4.1,
            "wind_direction": 100,
        },

        "screened_candidates": [
            {
                "facility_id": "FAC-001",
                "facility_name": "Alpha Cement Works",
                "distance_km": 1.55,
                "bearing_degrees": 44.25,
                "wind_direction": 100,
                "direction_difference": 55.75,
                "is_directionally_aligned": False,
            },
            {
                "facility_id": "FAC-002",
                "facility_name": "Beta Thermal Plant",
                "distance_km": 3.10,
                "bearing_degrees": 44.24,
                "wind_direction": 100,
                "direction_difference": 55.76,
                "is_directionally_aligned": False,
            },
            {
                "facility_id": "FAC-003",
                "facility_name": "Gamma Chemical Industries",
                "distance_km": 4.66,
                "bearing_degrees": 44.24,
                "wind_direction": 100,
                "direction_difference": 55.76,
                "is_directionally_aligned": False,
            },
        ],

        "investigation_plan": {
            "recommendations": [
                {
                    "facility_id": "FAC-001",
                    "facility_name": "Alpha Cement Works",
                    "priority_score": 36.9,
                    "priority_level": "medium",
                    "directionally_aligned": False,
                },
                {
                    "facility_id": "FAC-002",
                    "facility_name": "Beta Thermal Plant",
                    "priority_score": 33.8,
                    "priority_level": "medium",
                    "directionally_aligned": False,
                },
                {
                    "facility_id": "FAC-003",
                    "facility_name": "Gamma Chemical Industries",
                    "priority_score": 30.68,
                    "priority_level": "medium",
                    "directionally_aligned": False,
                },
            ],
            "decision_note": (
                "Scores represent screening priority, "
                "not proof of causation."
            ),
        },

        "data_source": "synthetic_demo_dataset",
    }

    print("\nSending investigation data to Qwen...\n")

    interpretation = await interpreter.interpret(sample_result)

    assert isinstance(interpretation, LLMInterpretation)

    print("=" * 60)
    print("STRUCTURED LLM INVESTIGATION INTERPRETATION")
    print("=" * 60)

    print(interpretation.model_dump_json(indent=2))

    print("\n--- STRUCTURE VALIDATION ---")
    print("Pydantic validation: PASSED")
    print("Ambient analysis:", bool(interpretation.ambient_analysis))
    print("Wind analysis:", bool(interpretation.wind_analysis))
    print("Facility analysis:", bool(interpretation.facility_analysis))
    print("Limitations:", len(interpretation.limitations))
    print("Recommendations:", len(interpretation.recommendations))

    print("\nSTRUCTURED OUTPUT TEST COMPLETED")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
