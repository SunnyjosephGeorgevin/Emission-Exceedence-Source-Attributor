
from src.database.checkpoint_repository import CheckpointRepository


class RecoveryService:

    RECOVERY_ACTIONS = {
        "data_retrieved": "resume_python_investigation",
        "python_investigation_completed": "resume_llm_interpretation",
        "llm_interpretation_completed": "finalize_for_human_approval",
    }

    def __init__(self):
        self.checkpoint_repository = CheckpointRepository()

    async def find_interrupted_investigations(
        self,
        limit: int = 10,
    ) -> list[dict]:

        return await self.checkpoint_repository.get_recoverable_investigations(
            limit=limit
        )

    async def prepare_recovery(
        self,
        investigation_id: int,
    ) -> dict:

        recovery_data = (
            await self.checkpoint_repository.get_recovery_state(
                investigation_id
            )
        )

        if recovery_data is None:
            raise ValueError(
                f"Investigation {investigation_id} not found."
            )

        investigation = recovery_data["investigation"]
        checkpoint = recovery_data["checkpoint"]
        state = recovery_data["reconstructed_state"]

        # Accept running for direct service use and recovering
        # for investigations claimed by the Supervisor.
        if investigation["status"] not in {
            "running",
            "recovering",
        }:
            raise ValueError(
                "Only investigations with running status "
                "can be recovered."
            )

        if checkpoint is None or state is None:
            raise ValueError(
                "Investigation has no saved checkpoint "
                "and cannot be resumed safely."
            )

        stage = checkpoint["stage"]

        if stage not in self.RECOVERY_ACTIONS:
            raise ValueError(
                f"Unsupported recovery stage: {stage}"
            )

        return {
            "investigation_id": investigation["id"],
            "station_id": investigation["station_id"],
            "status": investigation["status"],
            "recovery_stage": stage,
            "next_action": self.RECOVERY_ACTIONS[stage],
            "reconstructed_state": state,
            "recovery_ready": True,
        }
