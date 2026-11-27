from mcp.server.fastmcp import FastMCP

from src.data.sample_data import AIR_QUALITY_READINGS


# Initialize the MCP server.
mcp = FastMCP("Air Quality Server")


@mcp.tool()
def get_station_readings(station_id: str) -> list[dict]:
    """
    Retrieve air-quality readings for a monitoring station.
    """

    readings = []

    for reading in AIR_QUALITY_READINGS:
        if reading.station_id == station_id:
            readings.append({
                "station_id": reading.station_id,
                "timestamp": reading.timestamp.isoformat(),
                "pm25": reading.pm25,
                "pm10": reading.pm10,
                "so2": reading.so2,
                "nox": reading.nox,
            })

    return readings


if __name__ == "__main__":
    mcp.run()