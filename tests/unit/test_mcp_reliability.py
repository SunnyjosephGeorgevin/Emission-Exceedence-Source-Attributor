
import asyncio
from types import SimpleNamespace

import pytest

from src.services.mcp_data_provider import MCPDataProvider


def successful_response():
    return SimpleNamespace(
        isError=False,
        content=[
            SimpleNamespace(text='{"status": "success"}')
        ],
    )


def test_mcp_request_retries_and_succeeds():

    provider = MCPDataProvider(
        timeout_seconds=2,
        max_retries=2,
        retry_delay=0,
    )

    attempts = 0

    class FakeSession:

        async def call_tool(self, tool, arguments):

            nonlocal attempts
            attempts += 1

            if attempts == 1:
                raise RuntimeError("Temporary MCP failure")

            return successful_response()

    provider.sessions["air_quality"] = FakeSession()

    async def scenario():
        return await provider.call_tool(
            "air_quality",
            "get_station_readings",
            {"station_id": "ST-001"},
        )

    result = asyncio.run(scenario())

    assert attempts == 2
    assert result == [{"status": "success"}]


def test_mcp_request_times_out():

    provider = MCPDataProvider(
        timeout_seconds=0.05,
        max_retries=0,
        retry_delay=0,
    )

    attempts = 0

    class FakeSession:

        async def call_tool(self, tool, arguments):

            nonlocal attempts
            attempts += 1

            await asyncio.sleep(1)

            return successful_response()

    provider.sessions["air_quality"] = FakeSession()

    async def scenario():
        await provider.call_tool(
            "air_quality",
            "get_station_readings",
            {"station_id": "ST-001"},
        )

    with pytest.raises(
        RuntimeError,
        match="failed after 1 attempts",
    ):
        asyncio.run(scenario())

    assert attempts == 1


def test_mcp_request_fails_after_all_retries():

    provider = MCPDataProvider(
        timeout_seconds=2,
        max_retries=2,
        retry_delay=0,
    )

    attempts = 0

    class FakeSession:

        async def call_tool(self, tool, arguments):

            nonlocal attempts
            attempts += 1

            raise RuntimeError("MCP server unavailable")

    provider.sessions["air_quality"] = FakeSession()

    async def scenario():
        await provider.call_tool(
            "air_quality",
            "get_station_readings",
            {"station_id": "ST-001"},
        )

    with pytest.raises(
        RuntimeError,
        match="failed after 3 attempts",
    ):
        asyncio.run(scenario())

    assert attempts == 3
