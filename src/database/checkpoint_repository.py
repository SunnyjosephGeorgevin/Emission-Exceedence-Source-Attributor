
import json

from datetime import datetime, timezone

from src.database.connection import get_connection


class CheckpointRepository:

    # ==========================================================
    # SAVE CHECKPOINT
    # ==========================================================

    async def save_checkpoint(
        self,
        investigation_id: int,
        stage: str,
        state: dict,
    ) -> int:

        db = await get_connection()

        try:
            now = datetime.now(timezone.utc).isoformat()

            state_json = json.dumps(
                state,
                allow_nan=False,
            )

            cursor = await db.execute(
                """
                INSERT INTO investigation_checkpoints (
                    investigation_id,
                    stage,
                    state_json,
                    created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    investigation_id,
                    stage,
                    state_json,
                    now,
                ),
            )

            checkpoint_id = cursor.lastrowid

            await db.execute(
                """
                UPDATE investigations
                SET
                    current_stage = ?,
                    checkpoint_json = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    stage,
                    state_json,
                    now,
                    investigation_id,
                ),
            )

            await db.commit()

            return checkpoint_id

        except Exception:
            await db.rollback()
            raise

        finally:
            await db.close()

    # ==========================================================
    # GET LATEST CHECKPOINT
    # ==========================================================

    async def get_latest_checkpoint(
        self,
        investigation_id: int,
    ) -> dict | None:

        db = await get_connection()

        try:
            cursor = await db.execute(
                """
                SELECT *
                FROM investigation_checkpoints
                WHERE investigation_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (investigation_id,),
            )

            checkpoint = await cursor.fetchone()

            if checkpoint is None:
                return None

            result = dict(checkpoint)

            result["state"] = json.loads(
                result.pop("state_json")
            )

            return result

        finally:
            await db.close()

    # ==========================================================
    # GET CHECKPOINT HISTORY
    # ==========================================================

    async def get_checkpoint_history(
        self,
        investigation_id: int,
    ) -> list[dict]:

        db = await get_connection()

        try:
            cursor = await db.execute(
                """
                SELECT *
                FROM investigation_checkpoints
                WHERE investigation_id = ?
                ORDER BY id ASC
                """,
                (investigation_id,),
            )

            checkpoints = await cursor.fetchall()

            results = []

            for checkpoint in checkpoints:

                item = dict(checkpoint)

                item["state"] = json.loads(
                    item.pop("state_json")
                )

                results.append(item)

            return results

        finally:
            await db.close()

    # ==========================================================
    # FIND RECOVERABLE INVESTIGATIONS
    # ==========================================================

    async def get_recoverable_investigations(
        self,
        limit: int = 10,
    ) -> list[dict]:

        if (
            not isinstance(limit, int)
            or isinstance(limit, bool)
            or limit < 1
        ):
            raise ValueError(
                "Limit must be a positive integer."
            )

        db = await get_connection()

        try:
            cursor = await db.execute(
                """
                SELECT
                    id,
                    station_id,
                    station_latitude,
                    station_longitude,
                    status,
                    current_stage,
                    created_at,
                    updated_at
                FROM investigations
                WHERE status = 'running'
                ORDER BY updated_at ASC, id ASC
                LIMIT ?
                """,
                (limit,),
            )

            investigations = await cursor.fetchall()

            return [
                dict(investigation)
                for investigation in investigations
            ]

        finally:
            await db.close()

    # ==========================================================
    # ATOMIC RECOVERY CLAIM
    # ==========================================================

    async def claim_recovery(
        self,
        investigation_id: int,
    ) -> bool:
        """
        Atomically claim an interrupted investigation.

        Only one worker can change its status from
        running to recovering.

        Returns True when the claim succeeds.
        """

        db = await get_connection()

        try:
            now = datetime.now(timezone.utc).isoformat()

            cursor = await db.execute(
                """
                UPDATE investigations
                SET
                    status = 'recovering',
                    updated_at = ?
                WHERE
                    id = ?
                    AND status = 'running'
                """,
                (
                    now,
                    investigation_id,
                ),
            )

            await db.commit()

            return cursor.rowcount == 1

        except Exception:
            await db.rollback()
            raise

        finally:
            await db.close()

    # ==========================================================
    # RELEASE RECOVERY CLAIM
    # ==========================================================

    async def release_recovery(
        self,
        investigation_id: int,
    ) -> bool:
        """
        Release an unsuccessful recovery claim.

        The investigation returns to running so it can
        be retried during a later recovery attempt.
        """

        db = await get_connection()

        try:
            now = datetime.now(timezone.utc).isoformat()

            cursor = await db.execute(
                """
                UPDATE investigations
                SET
                    status = 'running',
                    updated_at = ?
                WHERE
                    id = ?
                    AND status = 'recovering'
                """,
                (
                    now,
                    investigation_id,
                ),
            )

            await db.commit()

            return cursor.rowcount == 1

        except Exception:
            await db.rollback()
            raise

        finally:
            await db.close()

    # ==========================================================
    # RESET STALE RECOVERY CLAIMS
    # ==========================================================

    async def reset_recovery_claims(self) -> int:
        """
        Reset recovery claims left by a previous server process.

        IMPORTANT:
        Call only once during startup in a single-worker
        application deployment.
        """

        db = await get_connection()

        try:
            now = datetime.now(timezone.utc).isoformat()

            cursor = await db.execute(
                """
                UPDATE investigations
                SET
                    status = 'running',
                    updated_at = ?
                WHERE status = 'recovering'
                """,
                (now,),
            )

            await db.commit()

            return cursor.rowcount

        except Exception:
            await db.rollback()
            raise

        finally:
            await db.close()

    # ==========================================================
    # RECONSTRUCT RECOVERY STATE
    # ==========================================================

    async def get_recovery_state(
        self,
        investigation_id: int,
    ) -> dict | None:
        """
        Reconstruct the saved state of an investigation.

        Returns:
            investigation:
                Investigation metadata, including station coordinates.

            checkpoint:
                Latest checkpoint metadata and decoded state.

            reconstructed_state:
                Decoded checkpoint state.
        """

        db = await get_connection()

        try:
            cursor = await db.execute(
                """
                SELECT
                    id,
                    station_id,
                    station_latitude,
                    station_longitude,
                    status,
                    current_stage,
                    created_at,
                    updated_at,
                    error_message
                FROM investigations
                WHERE id = ?
                """,
                (investigation_id,),
            )

            investigation = await cursor.fetchone()

            if investigation is None:
                return None

            investigation_data = dict(investigation)

            cursor = await db.execute(
                """
                SELECT *
                FROM investigation_checkpoints
                WHERE investigation_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (investigation_id,),
            )

            checkpoint = await cursor.fetchone()

            if checkpoint is None:

                return {
                    "investigation": investigation_data,
                    "checkpoint": None,
                    "reconstructed_state": None,
                }

            checkpoint_data = dict(checkpoint)

            reconstructed_state = json.loads(
                checkpoint_data.pop("state_json")
            )

            checkpoint_data["state"] = reconstructed_state

            return {
                "investigation": investigation_data,
                "checkpoint": checkpoint_data,
                "reconstructed_state": reconstructed_state,
            }

        finally:
            await db.close()
