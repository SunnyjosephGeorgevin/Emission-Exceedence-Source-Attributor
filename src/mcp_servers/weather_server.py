from mcp.server.fastmcp import FastMCP

from src.data.sample_data import WIND_READINGS


mcp = FastMCP("Weather Server")


@mcp.tool()
def get_wind_history() -> list[dict]:
    """
    Retrieve historical wind speed and direction readings.
    """

    readings = []

    for reading in WIND_READINGS:
        readings.append({
            "timestamp": reading.timestamp.isoformat(),
            "wind_speed": reading.wind_speed,
            "wind_direction": reading.wind_direction,
        })

    return readings


if __name__ == "__main__":
    mcp.run()
    