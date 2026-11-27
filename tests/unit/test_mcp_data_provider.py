
import asyncio

import pytest

from src.services.mcp_data_provider import MCPDataProvider
from src.data.models import (
    AirQualityReading,
    WindReading,
    IndustrialFacility,
)


def test_fetch_environmental_data_runs_initial_requests_concurrently():

    provider = MCPDataProvider()

    started_requests = 0
    all_started = asyncio.Event()

    async def fake_call_tool(server, tool, arguments):

        nonlocal started_requests

        if tool in {
            "get_station_readings",
            "get_wind_history",
            "get_stack_locations",
        }:
            started_requests += 1

            if started_requests == 3:
                all_started.set()

            await asyncio.wait_for(
                all_started.wait(),
                timeout=2,
            )

        if tool == "get_station_readings":
            return [{
                "station_id": "ST-001",
                "timestamp": "2026-11-25T10:00:00+00:00",
                "pm25": 180,
                "pm10": 240,
                "so2": 48,
                "nox": 85,
            }]

        if tool == "get_wind_history":
            return [{
                "timestamp": "2026-11-25T10:00:00+00:00",
                "wind_speed": 4.1,
                "wind_direction": 100,
            }]

        if tool == "get_stack_locations":
            return [{
                "facility_id": "FAC-001",
                "facility_name": "Alpha Cement Works",
                "industry_type": "Cement Manufacturing",
                "latitude": 13.09,
                "longitude": 80.27,
            }]

        if tool == "get_permit_limits":
            return [{
                "facility_id": arguments["facility_id"],
                "permitted_pm25": 80,
                "permitted_so2": 50,
                "data_source": "synthetic_demo_dataset",
            }]

        raise ValueError(f"Unexpected tool: {tool}")

    provider.call_tool = fake_call_tool

    async def scenario():
        return await provider.fetch_environmental_data("ST-001")

    air, wind, facilities = asyncio.run(scenario())

    assert started_requests == 3

    assert len(air) == 1
    assert isinstance(air[0], AirQualityReading)

    assert len(wind) == 1
    assert isinstance(wind[0], WindReading)

    assert len(facilities) == 1
    assert isinstance(facilities[0], IndustrialFacility)

    assert facilities[0].facility_id == "FAC-001"
    assert facilities[0].permitted_pm25 == 80


def test_fetch_environmental_data_handles_missing_permit_data():

    provider = MCPDataProvider()

    async def fake_call_tool(server, tool, arguments):

        if tool == "get_station_readings":
            return []

        if tool == "get_wind_history":
            return []

        if tool == "get_stack_locations":
            return [{
                "facility_id": "FAC-001",
                "facility_name": "Alpha Cement Works",
                "industry_type": "Cement Manufacturing",
                "latitude": 13.09,
                "longitude": 80.27,
            }]

        if tool == "get_permit_limits":
            return [{"error": "Facility not found"}]

        raise ValueError(f"Unexpected tool: {tool}")

    provider.call_tool = fake_call_tool

    async def scenario():
        await provider.fetch_environmental_data("ST-001")

    with pytest.raises(RuntimeError, match="Permit data unavailable"):
        asyncio.run(scenario())


def test_fetch_environmental_data_propagates_mcp_failure():

    provider = MCPDataProvider()

    async def fake_call_tool(server, tool, arguments):

        if tool == "get_station_readings":
            raise RuntimeError("MCP tool failed")

        if tool == "get_wind_history":
            return []

        if tool == "get_stack_locations":
            return []

        raise ValueError(f"Unexpected tool: {tool}")

    provider.call_tool = fake_call_tool

    async def scenario():
        await provider.fetch_environmental_data("ST-001")

    with pytest.raises(RuntimeError, match="MCP tool failed"):
        asyncio.run(scenario())
