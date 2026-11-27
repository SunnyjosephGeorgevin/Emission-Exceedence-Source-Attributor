import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[
            "-m",
            "src.mcp_servers.facility_server",
        ],
    )

    print("Connecting to Facility MCP Server...")

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            print("\nMCP connection established!")

            # Discover available tools.
            tools_response = await session.list_tools()

            print("\n--- AVAILABLE MCP TOOLS ---")

            for tool in tools_response.tools:
                print(f"Tool: {tool.name}")
                print(f"Description: {tool.description}")

            # Test tool 1: Retrieve facility locations.
            print("\n--- CALLING get_stack_locations ---")

            locations = await session.call_tool(
                "get_stack_locations",
                arguments={},
            )

            for content in locations.content:
                if hasattr(content, "text"):
                    print(content.text)

            # Test tool 2: Retrieve permit-related data.
            print("\n--- CALLING get_permit_limits ---")

            permit_data = await session.call_tool(
                "get_permit_limits",
                arguments={
                    "facility_id": "FAC-001"
                },
            )

            for content in permit_data.content:
                if hasattr(content, "text"):
                    print(content.text)


if __name__ == "__main__":
    asyncio.run(main())