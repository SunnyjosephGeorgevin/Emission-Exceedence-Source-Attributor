import asyncio
import sys

from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def connect_server(stack, server_name, module_name):

    print(f"\nConnecting to {server_name}...")

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", module_name],
    )

    read, write = await stack.enter_async_context(
        stdio_client(server_params)
    )

    session = await stack.enter_async_context(
        ClientSession(read, write)
    )

    await session.initialize()

    print(f"{server_name} connected successfully!")

    return session


async def main():

    async with AsyncExitStack() as stack:

        # Connect to all three MCP servers.
        air_quality_session = await connect_server(
            stack,
            "Air Quality Server",
            "src.mcp_servers.air_quality_server",
        )

        weather_session = await connect_server(
            stack,
            "Weather Server",
            "src.mcp_servers.weather_server",
        )

        facility_session = await connect_server(
            stack,
            "Facility Server",
            "src.mcp_servers.facility_server",
        )

        # Discover tools from every server.
        sessions = {
            "Air Quality": air_quality_session,
            "Weather": weather_session,
            "Facility": facility_session,
        }

        print("\n========== DISCOVERED MCP TOOLS ==========")

        for server_name, session in sessions.items():

            response = await session.list_tools()

            for tool in response.tools:
                print(f"{server_name}: {tool.name}")

        # Invoke air-quality tool.
        print("\n========== AIR QUALITY DATA ==========")

        air_result = await air_quality_session.call_tool(
            "get_station_readings",
            arguments={"station_id": "ST-001"},
        )

        print(air_result.content)

        # Invoke weather tool.
        print("\n========== WEATHER DATA ==========")

        weather_result = await weather_session.call_tool(
            "get_wind_history",
            arguments={},
        )

        print(weather_result.content)

        # Invoke facility location tool.
        print("\n========== FACILITY LOCATIONS ==========")

        facility_result = await facility_session.call_tool(
            "get_stack_locations",
            arguments={},
        )

        print(facility_result.content)

        # Invoke facility permit-related tool.
        print("\n========== FACILITY PERMIT DATA ==========")

        permit_result = await facility_session.call_tool(
            "get_permit_limits",
            arguments={"facility_id": "FAC-001"},
        )

        print(permit_result.content)

        print("\n========== ALL MCP OPERATIONS COMPLETED ==========")


if __name__ == "__main__":
    asyncio.run(main())
    