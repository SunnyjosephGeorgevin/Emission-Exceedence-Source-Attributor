
import asyncio
import copy
import json
import logging
import sys
import time

from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.data.models import (
    AirQualityReading,
    WindReading,
    IndustrialFacility,
)


logger = logging.getLogger(__name__)


class MCPDataProvider:

    def __init__(
        self,
        timeout_seconds: float = 15,
        max_retries: int = 2,
        retry_delay: float = 1,
    ):
        self.stack = AsyncExitStack()
        self.sessions = {}

        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # In-memory MCP monitoring metrics.
        self.metrics = {
            "total_calls": 0,
            "total_attempts": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "retries": 0,
            "total_attempt_duration_seconds": 0.0,
            "tools": {},
        }

    def _get_tool_metrics(self, tool: str):

        if tool not in self.metrics["tools"]:
            self.metrics["tools"][tool] = {
                "calls": 0,
                "attempts": 0,
                "successes": 0,
                "failures": 0,
                "retries": 0,
                "total_attempt_duration_seconds": 0.0,
                "last_attempt_duration_seconds": 0.0,
            }

        return self.metrics["tools"][tool]

    def get_metrics(self) -> dict:
        """
        Return a snapshot of the current MCP monitoring metrics.
        """

        return copy.deepcopy(self.metrics)

    async def connect_server(self, name: str, module: str):

        logger.info("Connecting to MCP server: %s", name)

        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", module],
        )

        read, write = await self.stack.enter_async_context(
            stdio_client(server_params)
        )

        session = await self.stack.enter_async_context(
            ClientSession(read, write)
        )

        await session.initialize()

        self.sessions[name] = session

        logger.info("Connected to MCP server: %s", name)

    async def connect_all(self):

        start_time = time.perf_counter()

        await self.connect_server(
            "air_quality",
            "src.mcp_servers.air_quality_server",
        )

        await self.connect_server(
            "weather",
            "src.mcp_servers.weather_server",
        )

        await self.connect_server(
            "facility",
            "src.mcp_servers.facility_server",
        )

        elapsed = time.perf_counter() - start_time

        logger.info(
            "All MCP servers connected in %.4f seconds",
            elapsed,
        )

    async def call_tool(
        self,
        server: str,
        tool: str,
        arguments: dict,
    ):

        total_attempts = self.max_retries + 1

        self.metrics["total_calls"] += 1

        tool_metrics = self._get_tool_metrics(tool)
        tool_metrics["calls"] += 1

        call_start = time.perf_counter()

        for attempt in range(1, total_attempts + 1):

            self.metrics["total_attempts"] += 1
            tool_metrics["attempts"] += 1

            attempt_start = time.perf_counter()

            try:

                logger.info(
                    "Calling MCP tool %s on %s (attempt %s/%s)",
                    tool,
                    server,
                    attempt,
                    total_attempts,
                )

                result = await asyncio.wait_for(
                    self.sessions[server].call_tool(
                        tool,
                        arguments=arguments,
                    ),
                    timeout=self.timeout_seconds,
                )

                if result.isError:
                    raise RuntimeError(
                        f"MCP tool returned an error: {tool}"
                    )

                records = []

                for content in result.content:

                    if hasattr(content, "text"):
                        records.append(json.loads(content.text))

                attempt_duration = (
                    time.perf_counter() - attempt_start
                )

                self.metrics[
                    "total_attempt_duration_seconds"
                ] += attempt_duration

                tool_metrics[
                    "total_attempt_duration_seconds"
                ] += attempt_duration

                tool_metrics[
                    "last_attempt_duration_seconds"
                ] = attempt_duration

                self.metrics["successful_calls"] += 1
                tool_metrics["successes"] += 1

                logger.info(
                    "MCP tool %s completed successfully in %.4f seconds",
                    tool,
                    attempt_duration,
                )

                return records

            except asyncio.CancelledError:
                raise

            except Exception as error:

                attempt_duration = (
                    time.perf_counter() - attempt_start
                )

                self.metrics[
                    "total_attempt_duration_seconds"
                ] += attempt_duration

                tool_metrics[
                    "total_attempt_duration_seconds"
                ] += attempt_duration

                tool_metrics[
                    "last_attempt_duration_seconds"
                ] = attempt_duration

                logger.warning(
                    "MCP tool %s failed on attempt %s/%s "
                    "after %.4f seconds: %s",
                    tool,
                    attempt,
                    total_attempts,
                    attempt_duration,
                    error,
                )

                if attempt == total_attempts:

                    self.metrics["failed_calls"] += 1
                    tool_metrics["failures"] += 1

                    total_duration = (
                        time.perf_counter() - call_start
                    )

                    logger.error(
                        "MCP tool %s permanently failed after "
                        "%s attempts. Total duration: %.4f seconds",
                        tool,
                        total_attempts,
                        total_duration,
                    )

                    raise RuntimeError(
                        f"MCP tool {tool} failed after "
                        f"{total_attempts} attempts."
                    ) from error

                self.metrics["retries"] += 1
                tool_metrics["retries"] += 1

                delay = self.retry_delay * (2 ** (attempt - 1))

                logger.info(
                    "Retrying MCP tool %s in %.2f seconds",
                    tool,
                    delay,
                )

                await asyncio.sleep(delay)

    async def _build_facility(self, item: dict) -> IndustrialFacility:

        permit_data = await self.call_tool(
            "facility",
            "get_permit_limits",
            {"facility_id": item["facility_id"]},
        )

        if not permit_data or "error" in permit_data[0]:
            raise RuntimeError(
                f'Permit data unavailable for {item["facility_id"]}'
            )

        permit = permit_data[0]

        return IndustrialFacility(
            **item,
            permitted_pm25=permit["permitted_pm25"],
            permitted_so2=permit["permitted_so2"],
        )

    async def fetch_environmental_data(self, station_id: str):

        logger.info(
            "Starting environmental data retrieval for station %s",
            station_id,
        )

        retrieval_start = time.perf_counter()

        air_data, wind_data, facility_data = await asyncio.gather(

            self.call_tool(
                "air_quality",
                "get_station_readings",
                {"station_id": station_id},
            ),

            self.call_tool(
                "weather",
                "get_wind_history",
                {},
            ),

            self.call_tool(
                "facility",
                "get_stack_locations",
                {},
            ),
        )

        air_readings = [
            AirQualityReading(**item)
            for item in air_data
        ]

        wind_readings = [
            WindReading(**item)
            for item in wind_data
        ]

        facilities = await asyncio.gather(
            *[
                self._build_facility(item)
                for item in facility_data
            ]
        )

        elapsed = time.perf_counter() - retrieval_start

        logger.info(
            "Environmental data retrieval completed in %.4f seconds",
            elapsed,
        )

        logger.info(
            "Retrieved %s air readings, %s wind readings, "
            "and %s facility records",
            len(air_readings),
            len(wind_readings),
            len(facilities),
        )

        return air_readings, wind_readings, list(facilities)

    async def close(self):

        logger.info("Closing MCP connections")

        await self.stack.aclose()

        logger.info("MCP connections closed")
