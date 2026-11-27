class InspectionPlanner:

    def __init__(self, max_distance_km: float = 20.0):
        self.max_distance_km = max_distance_km

    def calculate_score(self, candidate: dict) -> float:
        """
        Calculate a transparent screening priority score.

        This is NOT a probability of responsibility.
        """

        distance = candidate["distance_km"]

        # Proximity score: closer facilities receive a higher score.
        proximity_score = max(
            0.0,
            1 - distance / self.max_distance_km
        ) * 40

        # Directional alignment is a screening signal.
        wind_score = (
            60.0
            if candidate["is_directionally_aligned"]
            else 0.0
        )

        return round(proximity_score + wind_score, 2)

    def generate_plan(
        self,
        exceedance_result: dict,
        candidates: list[dict],
        facility_profiles: list[dict],
    ) -> dict:

        if not exceedance_result["is_exceedance"]:
            return {
                "status": "no_exceedance",
                "message": "No pollution exceedance detected.",
                "recommendations": [],
            }

        profile_lookup = {
            profile["facility_id"]: profile
            for profile in facility_profiles
        }

        recommendations = []

        for candidate in candidates:

            score = self.calculate_score(candidate)

            profile = profile_lookup.get(
                candidate["facility_id"]
            )

            if profile is None:
                continue

            recommendations.append({
                "facility_id": candidate["facility_id"],
                "facility_name": candidate["facility_name"],
                "priority_score": score,
                "priority_level": (
                    "high" if score >= 60
                    else "medium" if score >= 30
                    else "low"
                ),
                "distance_km": candidate["distance_km"],
                "directionally_aligned": (
                    candidate["is_directionally_aligned"]
                ),
                "industry_type": profile["industry_type"],
                "supporting_evidence": [
                    "Facility is within the configured screening distance.",
                    (
                        "Facility bearing is aligned with wind-from direction."
                        if candidate["is_directionally_aligned"]
                        else "Facility is not aligned with the observed wind direction."
                    ),
                ],
            })

        recommendations.sort(
            key=lambda item: item["priority_score"],
            reverse=True,
        )

        return {
            "status": "investigation_completed",
            "station_id": exceedance_result["station_id"],
            "exceedance_count": exceedance_result["exceedance_count"],
            "pollutants": [
                item["pollutant"]
                for item in exceedance_result["exceedances"]
            ],
            "recommendations": recommendations,
            "decision_note": (
                "Scores represent screening priority, not "
                "probability of responsibility or proof of causation."
            ),
        }