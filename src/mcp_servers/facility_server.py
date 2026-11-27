from mcp.server.fastmcp import FastMCP

from src.data.sample_data import INDUSTRIAL_FACILITIES


mcp = FastMCP("Facility Server")


@mcp.tool()
def get_stack_locations() -> list[dict]:
    """
    Retrieve industrial facility locations.
    """

    locations = []

    for facility in INDUSTRIAL_FACILITIES:
        locations.append({
            "facility_id": facility.facility_id,
            "facility_name": facility.facility_name,
            "latitude": facility.latitude,
            "longitude": facility.longitude,
            "industry_type": facility.industry_type,
        })

    return locations


@mcp.tool()
def get_permit_limits(facility_id: str) -> dict:
    """
    Retrieve demonstration permit-related values for a facility.
    """

    for facility in INDUSTRIAL_FACILITIES:
        if facility.facility_id == facility_id:
            return {
                "facility_id": facility.facility_id,
                "permitted_pm25": facility.permitted_pm25,
                "permitted_so2": facility.permitted_so2,
                "data_source": "synthetic_demo_dataset",
            }

    return {
        "error": f"Facility {facility_id} not found."
    }


if __name__ == "__main__":
    mcp.run()
    