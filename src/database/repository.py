
import json

from datetime import datetime, timezone

from src.database.connection import get_connection


_UNSET = object()


class InvestigationRepository:

    async def create_investigation(
        self,
        station_id: str,
        status: str = "pending",
        current_stage: str = "pending",
        station_latitude: float | None = None,
        station_longitude: float | None = None,
    ) -> int:

        if (station_latitude is None) != (station_longitude is None):
            raise ValueError(
                "Both station latitude and longitude must be provided together."
            )

        if station_latitude is not None:
            if not -90 <= station_latitude <= 90:
                raise ValueError("Invalid station latitude.")

            if not -180 <= station_longitude <= 180:
                raise ValueError("Invalid station longitude.")

        db = await get_connection()

        try:
            now = datetime.now(timezone.utc).isoformat()

            cursor = await db.execute(
                """
                INSERT INTO investigations (
                    station_id,
                    station_latitude,
                    station_longitude,
                    status,
                    current_stage,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    station_id,
                    station_latitude,
                    station_longitude,
                    status,
                    current_stage,
                    now,
                    now,
                ),
            )

            investigation_id = cursor.lastrowid

            await db.commit()

            return investigation_id

        except Exception:
            await db.rollback()
            raise

        finally:
            await db.close()

    async def update_investigation(
        self,
        investigation_id: int,
        status: str,
        current_stage: str,
        execution_seconds: float | None = None,
        mcp_metrics: dict | None = None,
        result_data=_UNSET,
        error_message: str | None = None,
    ) -> None:

        db = await get_connection()

        try:
            now = datetime.now(timezone.utc).isoformat()

            if result_data is _UNSET:
                result_json = None
                update_result = False
            else:
                result_json = (
                    json.dumps(result_data, allow_nan=False)
                    if result_data is not None
                    else None
                )
                update_result = True

            cursor = await db.execute(
                """
                UPDATE investigations
                SET
                    status = ?,
                    current_stage = ?,
                    execution_seconds = ?,
                    updated_at = ?,
                    error_message = ?,
                    result_json = CASE
                        WHEN ? = 1 THEN ?
                        ELSE result_json
                    END
                WHERE id = ?
                """,
                (
                    status,
                    current_stage,
                    execution_seconds,
                    now,
                    error_message,
                    int(update_result),
                    result_json,
                    investigation_id,
                ),
            )

            if cursor.rowcount == 0:
                raise ValueError(
                    f"Investigation {investigation_id} not found."
                )

            if mcp_metrics is not None:

                await db.execute(
                    """
                    DELETE FROM mcp_tool_metrics
                    WHERE investigation_id = ?
                    """,
                    (investigation_id,),
                )

                await self._save_tool_metrics(
                    db,
                    investigation_id,
                    mcp_metrics,
                )

            await db.commit()

        except Exception:
            await db.rollback()
            raise

        finally:
            await db.close()

    async def _save_tool_metrics(
        self,
        db,
        investigation_id: int,
        mcp_metrics: dict,
    ):

        for tool_name, tool_data in (
            mcp_metrics.get("tools", {}).items()
        ):

            await db.execute(
                """
                INSERT INTO mcp_tool_metrics (
                    investigation_id,
                    tool_name,
                    calls,
                    attempts,
                    successes,
                    failures,
                    retries,
                    total_duration_seconds,
                    last_duration_seconds
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    investigation_id,
                    tool_name,
                    tool_data.get("calls", 0),
                    tool_data.get("attempts", 0),
                    tool_data.get("successes", 0),
                    tool_data.get("failures", 0),
                    tool_data.get("retries", 0),
                    tool_data.get(
                        "total_attempt_duration_seconds", 0.0
                    ),
                    tool_data.get(
                        "last_attempt_duration_seconds", 0.0
                    ),
                ),
            )

    async def save_investigation(
        self,
        station_id: str,
        status: str,
        execution_seconds: float,
        mcp_metrics: dict,
        result_data: dict | None = None,
        station_latitude: float | None = None,
        station_longitude: float | None = None,
    ) -> int:

        investigation_id = await self.create_investigation(
            station_id=station_id,
            status=status,
            current_stage="completed",
            station_latitude=station_latitude,
            station_longitude=station_longitude,
        )

        await self.update_investigation(
            investigation_id=investigation_id,
            status=status,
            current_stage="completed",
            execution_seconds=execution_seconds,
            mcp_metrics=mcp_metrics,
            result_data=result_data,
        )

        return investigation_id

    async def get_investigation(
        self,
        investigation_id: int,
    ) -> dict | None:

        db = await get_connection()

        try:
            cursor = await db.execute(
                """
                SELECT *
                FROM investigations
                WHERE id = ?
                """,
                (investigation_id,),
            )

            investigation = await cursor.fetchone()

            if investigation is None:
                return None

            investigation_data = dict(investigation)

            result_json = investigation_data.get("result_json")

            investigation_data["result_data"] = (
                json.loads(result_json)
                if result_json is not None
                else None
            )

            cursor = await db.execute(
                """
                SELECT *
                FROM mcp_tool_metrics
                WHERE investigation_id = ?
                """,
                (investigation_id,),
            )

            metrics = await cursor.fetchall()

            return {
                "investigation": investigation_data,
                "tool_metrics": [
                    dict(metric)
                    for metric in metrics
                ],
            }

        finally:
            await db.close()

    async def get_recent_investigations(
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
                SELECT *
                FROM investigations
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            )

            investigations = await cursor.fetchall()

            results = []

            for investigation in investigations:

                item = dict(investigation)

                result_json = item.get("result_json")

                item["result_data"] = (
                    json.loads(result_json)
                    if result_json is not None
                    else None
                )

                results.append(item)

            return results

        finally:
            await db.close()


    async def get_aggregate_mcp_metrics(self) -> dict:
        db = await get_connection()

        try:
            cursor = await db.execute(
                """
                SELECT
                    COALESCE(SUM(calls), 0) AS total_calls,
                    COALESCE(SUM(attempts), 0) AS total_attempts,
                    COALESCE(SUM(successes), 0) AS successful_calls,
                    COALESCE(SUM(failures), 0) AS failed_calls,
                    COALESCE(SUM(retries), 0) AS retries,
                    COALESCE(SUM(total_duration_seconds), 0.0)
                        AS total_duration_seconds
                FROM mcp_tool_metrics
                """
            )

            totals = dict(await cursor.fetchone())

            cursor = await db.execute(
                """
                SELECT
                    tool_name,
                    SUM(calls) AS calls,
                    SUM(attempts) AS attempts,
                    SUM(successes) AS successes,
                    SUM(failures) AS failures,
                    SUM(retries) AS retries,
                    SUM(total_duration_seconds)
                        AS total_duration_seconds
                FROM mcp_tool_metrics
                GROUP BY tool_name
                ORDER BY tool_name
                """
            )

            tool_rows = await cursor.fetchall()

            total_attempts = totals["total_attempts"]
            total_decisions = (
                totals["successful_calls"] + totals["failed_calls"]
            )

            return {
                **totals,
                "average_duration_seconds": (
                    totals["total_duration_seconds"] / total_attempts
                    if total_attempts else 0.0
                ),
                "success_rate": (
                    totals["successful_calls"] / total_decisions * 100
                    if total_decisions else 0.0
                ),
                "tools": {
                    row["tool_name"]: dict(row)
                    for row in tool_rows
                },
            }

        finally:
            await db.close()
