import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():

    # Configure how the client launches the MCP server.
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[
            "-m",
            "src.mcp_servers.air_quality_server",
        ],
    )

    print("Connecting to Air Quality MCP Server...")

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            # Initialize MCP connection.
            await session.initialize()

            print("\nMCP connection established!")

            # Discover available tools.
            tools_response = await session.list_tools()

            print("\n--- AVAILABLE MCP TOOLS ---")

            for tool in tools_response.tools:
                print(f"Tool: {tool.name}")
                print(f"Description: {tool.description}")

            # Invoke the discovered tool.
            print("\n--- CALLING AIR QUALITY TOOL ---")

            result = await session.call_tool(
                "get_station_readings",
                arguments={
                    "station_id": "ST-001"
                },
            )

            for content in result.content:
                if hasattr(content, "text"):
                    print(content.text)


if __name__ == "__main__":
    asyncio.run(main())