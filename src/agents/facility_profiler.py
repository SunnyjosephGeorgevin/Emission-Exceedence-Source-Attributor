from src.data.models import IndustrialFacility


class FacilityProfiler:

    def profile(
        self,
        facility_id: str,
        facilities: list[IndustrialFacility],
    ) -> dict | None:
        """
        Retrieve the available industrial information
        for a particular facility.
        """

        for facility in facilities:

            if facility.facility_id == facility_id:

                return {
                    "facility_id": facility.facility_id,
                    "facility_name": facility.facility_name,
                    "industry_type": facility.industry_type,
                    "location": {
                        "latitude": facility.latitude,
                        "longitude": facility.longitude,
                    },
                    "permit_information": {
                        "permitted_pm25": facility.permitted_pm25,
                        "permitted_so2": facility.permitted_so2,
                    },
                    "data_source": "synthetic_demo_dataset",
                    "profile_status": "success",
                }

        return None

    def profile_all(
        self,
        facilities: list[IndustrialFacility],
    ) -> list[dict]:
        """Generate profiles for all available facilities."""

        profiles = []

        for facility in facilities:

            profile = self.profile(
                facility.facility_id,
                facilities,
            )

            if profile is not None:
                profiles.append(profile)

        return profiles