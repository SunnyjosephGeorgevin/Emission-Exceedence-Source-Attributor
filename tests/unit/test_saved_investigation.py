
import asyncio

from src.database.repository import InvestigationRepository


def test_retrieve_supervisor_investigation():

    async def main():

        repository = InvestigationRepository()

        result = await repository.get_investigation(1)

        assert result is not None

        investigation = result["investigation"]

        assert investigation["station_id"] == "ST-001"

        assert investigation["status"] == "awaiting_approval"

        assert isinstance(result["tool_metrics"], list)

        return result

    result = asyncio.run(main())

    assert result is not None
