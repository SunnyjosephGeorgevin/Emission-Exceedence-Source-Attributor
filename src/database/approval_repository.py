
from datetime import datetime, timezone

from src.database.connection import get_connection


class ApprovalRepository:

    async def submit_decision(
        self,
        investigation_id: int,
        decision: str,
        reviewer: str,
        comments: str | None = None,
    ) -> dict:

        # Validate the decision before accessing the database.
        if decision not in {"approved", "rejected"}:
            raise ValueError(
                "Decision must be either 'approved' or 'rejected'."
            )

        if not isinstance(reviewer, str) or not reviewer.strip():
            raise ValueError("Reviewer name is required.")

        if comments is not None and not isinstance(comments, str):
            raise ValueError("Comments must be a string or None.")

        reviewer = reviewer.strip()
        now = datetime.now(timezone.utc).isoformat()

        db = await get_connection()

        try:
            # Acquire a write lock so concurrent reviewers cannot
            # submit conflicting decisions.
            await db.execute("BEGIN IMMEDIATE")

            cursor = await db.execute(
                """
                SELECT status
                FROM investigations
                WHERE id = ?
                """,
                (investigation_id,),
            )

            investigation = await cursor.fetchone()

            if investigation is None:
                raise ValueError(
                    f"Investigation {investigation_id} not found."
                )

            if investigation["status"] != "awaiting_approval":
                raise ValueError(
                    "Only investigations awaiting approval "
                    "can receive a decision."
                )

            # Save the human decision.
            await db.execute(
                """
                INSERT INTO investigation_approvals (
                    investigation_id,
                    decision,
                    reviewer,
                    comments,
                    decided_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    investigation_id,
                    decision,
                    reviewer,
                    comments,
                    now,
                ),
            )

            # Update the investigation status in the same transaction.
            cursor = await db.execute(
                """
                UPDATE investigations
                SET status = ?,
                    current_stage = ?,
                    updated_at = ?
                WHERE id = ?
                  AND status = 'awaiting_approval'
                """,
                (
                    decision,
                    decision,
                    now,
                    investigation_id,
                ),
            )

            if cursor.rowcount != 1:
                raise RuntimeError(
                    "Investigation status changed unexpectedly."
                )

            await db.commit()

            return {
                "investigation_id": investigation_id,
                "decision": decision,
                "reviewer": reviewer,
                "comments": comments,
                "decided_at": now,
                "status": decision,
            }

        except Exception:
            await db.rollback()
            raise

        finally:
            await db.close()

    async def get_approval(
        self,
        investigation_id: int,
    ) -> dict | None:

        db = await get_connection()

        try:
            cursor = await db.execute(
                """
                SELECT *
                FROM investigation_approvals
                WHERE investigation_id = ?
                """,
                (investigation_id,),
            )

            approval = await cursor.fetchone()

            if approval is None:
                return None

            return dict(approval)

        finally:
            await db.close()
