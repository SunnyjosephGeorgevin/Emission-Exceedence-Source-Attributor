
import asyncio
import json
import logging
import time

from ollama import AsyncClient

from src.core.config import OLLAMA_MODEL, OLLAMA_BASE_URL
from src.core.thresholds import AMBIENT_THRESHOLDS
from src.data.models import LLMInterpretation


logger = logging.getLogger(__name__)


class LLMInterpreter:

    def __init__(self):
        self.client = AsyncClient(host=OLLAMA_BASE_URL)
        self.model = OLLAMA_MODEL
        self.timeout_seconds = 90

    @staticmethod
    def _format_value(value):
        if isinstance(value, (int, float)):
            return f"{value:g}"
        return str(value)

    @classmethod
    def _build_ambient_analysis(cls, ambient_reading):
        if not ambient_reading:
            return "Ambient reading data is unavailable."

        lines = []

        pollutant_names = {
            "pm25": "PM2.5",
            "pm10": "PM10",
            "so2": "SO2",
            "nox": "NOx",
        }

        for key, display_name in pollutant_names.items():
            measured = ambient_reading.get(key)

            if measured is None:
                continue

            threshold = AMBIENT_THRESHOLDS.get(key)

            if threshold is None:
                lines.append(
                    f"{display_name}: measured value "
                    f"{cls._format_value(measured)}; "
                    "threshold not available."
                )
                continue

            status = (
                "exceeds the configured synthetic threshold"
                if measured > threshold
                else "is within the configured synthetic threshold"
            )

            lines.append(
                f"{display_name}: measured value "
                f"{cls._format_value(measured)}, configured "
                f"synthetic threshold "
                f"{cls._format_value(threshold)}; {status}."
            )

        lines.append(
            "These are synthetic demonstration values, "
            "not official regulatory measurements or standards."
        )

        return " ".join(lines)

    @classmethod
    def _build_wind_analysis(cls, wind_reading, candidates):
        if not wind_reading:
            return "Wind reading data is unavailable."

        parts = []

        speed = wind_reading.get("wind_speed")
        direction = wind_reading.get("wind_direction")

        if speed is not None:
            parts.append(
                f"Observed wind speed: {cls._format_value(speed)}. "
                "The measurement unit was not supplied."
            )

        if direction is not None:
            parts.append(
                f"Observed wind direction: "
                f"{cls._format_value(direction)} degrees."
            )

        parts.append(
            "Wind direction alone does not establish facility alignment."
        )

        if candidates:
            for facility in candidates:
                name = facility.get(
                    "facility_name",
                    facility.get("facility_id", "Unknown facility"),
                )

                aligned = facility.get("is_directionally_aligned")

                if aligned is True:
                    alignment = "directionally aligned"
                elif aligned is False:
                    alignment = "not directionally aligned"
                else:
                    alignment = "alignment not available"

                parts.append(f"{name}: {alignment}.")

        return " ".join(parts)

    @classmethod
    def _build_facility_analysis(cls, candidates, recommendations):
        if not candidates:
            return "No screened facility candidates are available."

        recommendations_by_id = {
            item.get("facility_id"): item
            for item in recommendations
            if item.get("facility_id")
        }

        lines = []

        for facility in candidates:
            facility_id = facility.get("facility_id")
            name = facility.get(
                "facility_name",
                facility_id or "Unknown facility",
            )

            recommendation = recommendations_by_id.get(
                facility_id, {}
            )

            distance = facility.get("distance_km")
            aligned = facility.get("is_directionally_aligned")
            score = recommendation.get("priority_score")
            priority = recommendation.get("priority_level")

            details = [f"{name} ({facility_id})"]

            if distance is not None:
                details.append(
                    f"distance: {cls._format_value(distance)} km"
                )

            if aligned is True:
                details.append("directionally aligned: Yes")
            elif aligned is False:
                details.append("directionally aligned: No")
            else:
                details.append("directional alignment: unavailable")

            if score is not None:
                details.append(
                    f"priority score: {cls._format_value(score)}"
                )

            if priority:
                details.append(f"priority level: {priority}")

            lines.append("; ".join(details) + ".")

        lines.append(
            "These scores represent screening priority only, "
            "not probability of responsibility or proof of causation."
        )

        return " ".join(lines)

    async def interpret(
        self,
        investigation_result: dict,
    ) -> LLMInterpretation:

        ambient_reading = investigation_result.get(
            "ambient_reading", {}
        )

        exceedance_result = investigation_result.get(
            "exceedance_result", {}
        )

        wind_reading = investigation_result.get("wind_reading")

        candidates = investigation_result.get(
            "screened_candidates", []
        ) or []

        investigation_plan = investigation_result.get(
            "investigation_plan", {}
        ) or {}

        recommendations = investigation_plan.get(
            "recommendations", []
        ) or []

        llm_input = {
            "station_id": investigation_result.get("station_id"),
            "investigation_timestamp": investigation_result.get(
                "investigation_timestamp"
            ),
            "ambient_reading": ambient_reading,
            "synthetic_thresholds": AMBIENT_THRESHOLDS,
            "exceedance_result": exceedance_result,
            "wind_reading": wind_reading,
            "screened_candidates": candidates,
            "investigation_plan": investigation_plan,
            "data_source": investigation_result.get("data_source"),
        }

        prompt = f"""
You are an environmental investigation report interpreter.

Interpret the supplied data using ONLY the supplied facts.

STRICT RULES:
1. Never invent measurements, units, distances, or directions.
2. Never add a unit to wind speed. If no unit is supplied,
   explicitly say that the unit is unspecified.
3. Include every supplied ambient pollutant, including pollutants
   that are below their configured thresholds.
4. Include every screened facility. Do not omit any candidate.
5. Preserve exact distances and priority scores.
6. Do not invent facility emissions or stack measurements.
7. All supplied data is synthetic demonstration data.
8. Thresholds are not official regulatory standards.
9. Ambient measurements are not factory stack measurements.
10. Never claim a facility caused pollution or violated a permit.
11. Screening scores are not probabilities.
12. Wind screening is simplified, not dispersion modelling.
13. Do not infer compass directions from wind degrees.
14. Facility alignment must follow the supplied alignment field.
15. Clearly state limitations and uncertainty.
16. Recommendations must be cautious and intended for human review.
17. Never recommend enforcement, penalties, or prosecution based
    only on screening results.

FIELD REQUIREMENTS:
- ambient_analysis: Explain all available pollutant readings,
  their configured thresholds, and exceedance status.
- wind_analysis: Report supplied wind measurements without
  inventing units. Explain the alignment status of every facility.
- facility_analysis: Describe EVERY facility, exact distance,
  alignment status, and priority score when available.
- limitations: List important evidence gaps.
- recommendations: Suggest evidence collection, monitoring,
  permit-record verification, and human-led inspection only.

Keep each explanation concise.
Do not use Markdown headings inside fields.
Return valid JSON matching the supplied schema.

INVESTIGATION DATA:
{json.dumps(llm_input, separators=(",", ":"))}
"""

        print(
            f"\nSending investigation data to {self.model}...",
            flush=True,
        )

        start_time = time.perf_counter()

        try:
            response = await asyncio.wait_for(
                self.client.chat(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    format=LLMInterpretation.model_json_schema(),
                    options={
                        "temperature": 0,
                        "num_predict": 1200,
                    },
                ),
                timeout=self.timeout_seconds,
            )

        except asyncio.TimeoutError as error:
            raise TimeoutError(
                f"Ollama interpretation exceeded "
                f"{self.timeout_seconds} seconds."
            ) from error

        elapsed_time = time.perf_counter() - start_time

        print(
            f"LLM response received in {elapsed_time:.2f} seconds.",
            flush=True,
        )

        raw_response = response.message.content

        try:
            validated_response = LLMInterpretation.model_validate_json(
                raw_response
            )

        except Exception as error:
            logger.error(
                "LLM returned invalid structured JSON: %s",
                error,
            )
            raise ValueError(
                "Ollama returned an incomplete or invalid JSON response."
            ) from error

        # Deterministic factual sections prevent the LLM from
        # omitting measurements, facilities, or inventing units.
        validated_response = validated_response.model_copy(
            update={
                "ambient_analysis": self._build_ambient_analysis(
                    ambient_reading
                ),
                "wind_analysis": self._build_wind_analysis(
                    wind_reading,
                    candidates,
                ),
                "facility_analysis": self._build_facility_analysis(
                    candidates,
                    recommendations,
                ),
            }
        )

        logger.info(
            "LLM interpretation completed in %.2f seconds.",
            elapsed_time,
        )

        return validated_response
