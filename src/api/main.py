from src.data.sample_data import INDUSTRIAL_FACILITIES

import asyncio
import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks, HTTPException

from src.api.schemas import (
    InvestigationRequest,
    ApprovalRequest,
)

from src.database.init_db import initialize_database
from src.database.repository import InvestigationRepository
from src.database.approval_repository import ApprovalRepository
from src.database.checkpoint_repository import CheckpointRepository

from src.orchestration.supervisor import Supervisor


logger = logging.getLogger(__name__)


# ==========================================================
# REPOSITORIES
# ==========================================================

investigation_repository = InvestigationRepository()
approval_repository = ApprovalRepository()
checkpoint_repository = CheckpointRepository()


# ==========================================================
# AUTOMATIC RECOVERY
# ==========================================================

async def recover_interrupted_investigation(
    investigation_id: int,
):
    """
    Reconstruct a Supervisor and resume an interrupted investigation.
    """

    try:

        recovery_data = await checkpoint_repository.get_recovery_state(
            investigation_id
        )

        if recovery_data is None:
            logger.warning(
                "Recovery data missing for investigation %s",
                investigation_id,
            )
            return

        state = recovery_data["reconstructed_state"]

        if state is None:
            logger.warning(
                "No checkpoint available for investigation %s",
                investigation_id,
            )
            return

        latitude = state.get("station_latitude")
        longitude = state.get("station_longitude")

        if latitude is None or longitude is None:
            logger.error(
                "Cannot recover investigation %s: station coordinates "
                "are missing from its checkpoint.",
                investigation_id,
            )
            return

        supervisor = Supervisor(
            station_latitude=latitude,
            station_longitude=longitude,
        )

        result = await supervisor.resume_investigation(
            investigation_id
        )

        logger.info(
            "Automatic recovery finished for investigation %s: %s",
            investigation_id,
            result.get("status"),
        )

    except Exception:

        logger.exception(
            "Automatic recovery failed for investigation %s",
            investigation_id,
        )


async def recover_interrupted_investigations():

    logger.info("Scanning for interrupted investigations.")

    # Recover claims left by a previous server process.
    reset_count = await checkpoint_repository.reset_recovery_claims()

    if reset_count:
        logger.warning(
            "Reset %s stale recovery claims.",
            reset_count,
        )

    interrupted = (
        await checkpoint_repository.get_recoverable_investigations(
            limit=100
        )
    )

    logger.info(
        "Found %s interrupted investigations.",
        len(interrupted),
    )

    tasks = []

    for investigation in interrupted:

        investigation_id = investigation["id"]

        task = asyncio.create_task(
            recover_interrupted_investigation(
                investigation_id
            ),
            name=f"recovery-{investigation_id}",
        )

        tasks.append(task)

    return tasks


# ==========================================================
# APPLICATION LIFESPAN
# ==========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Initializing Industrial Emission Exceedance API.")

    # Initialize tables and migrations.
    await initialize_database()

    app.state.recovery_tasks = []

    try:

        # Start recovery tasks after database initialization.
        app.state.recovery_tasks = (
            await recover_interrupted_investigations()
        )

        yield

    finally:

        # Allow active recovery tasks to finish before shutdown.
        tasks = app.state.recovery_tasks

        if tasks:

            logger.info(
                "Waiting for %s recovery tasks before shutdown.",
                len(tasks),
            )

            await asyncio.gather(
                *tasks,
                return_exceptions=True,
            )

        logger.info("Industrial Emission Exceedance API stopped.")


# ==========================================================
# FASTAPI APPLICATION
# ==========================================================

app = FastAPI(
    title="Industrial Emission Exceedance API",
    description=(
        "API for investigating industrial emission exceedances "
        "using a multi-agent source attribution workflow."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ==========================================================
# BACKGROUND INVESTIGATION EXECUTION
# ==========================================================

async def execute_investigation_background(
    investigation_id: int,
    station_id: str,
    station_latitude: float,
    station_longitude: float,
):

    logger.info(
        "Starting background investigation %s for station %s",
        investigation_id,
        station_id,
    )

    try:

        supervisor = Supervisor(
            station_latitude=station_latitude,
            station_longitude=station_longitude,
        )

        result = await supervisor.run_investigation_with_mcp(
            station_id=station_id,
            investigation_id=investigation_id,
        )

        logger.info(
            "Background investigation %s finished with status %s",
            investigation_id,
            result.get("status"),
        )

    except Exception as error:

        logger.exception(
            "Background investigation %s failed",
            investigation_id,
        )

        try:

            await investigation_repository.update_investigation(
                investigation_id=investigation_id,
                status="failed",
                current_stage="failed",
                error_message=str(error),
            )

        except Exception:

            logger.exception(
                "Could not update failed investigation %s",
                investigation_id,
            )


# ==========================================================
# HEALTH CHECK
# ==========================================================

@app.get("/")
async def root():

    return {
        "application": "Industrial Emission Exceedance",
        "status": "running",
        "message": "Industrial emission investigation API is operational.",
    }


# ==========================================================
# CREATE INVESTIGATION
# ==========================================================

@app.post(
    "/investigations",
    status_code=202,
)
async def create_investigation(
    request: InvestigationRequest,
    background_tasks: BackgroundTasks,
):

    try:

        investigation_id = (
            await investigation_repository.create_investigation(
                station_id=request.station_id,
                status="pending",
                current_stage="pending",
                station_latitude=request.station_latitude,
                station_longitude=request.station_longitude,
            )
        )

        background_tasks.add_task(
            execute_investigation_background,
            investigation_id,
            request.station_id,
            request.station_latitude,
            request.station_longitude,
        )

        logger.info(
            "Investigation %s accepted for background execution",
            investigation_id,
        )

        return {
            "investigation_id": investigation_id,
            "station_id": request.station_id,
            "status": "pending",
            "message": "Investigation accepted for background execution.",
            "status_url": f"/investigations/{investigation_id}",
        }

    except Exception as error:

        logger.exception("Could not create investigation")

        raise HTTPException(
            status_code=500,
            detail="Could not create investigation.",
        ) from error


# ==========================================================
# GET INVESTIGATION
# ==========================================================

@app.get("/investigations/{investigation_id}")
async def get_investigation(
    investigation_id: int,
):

    investigation = (
        await investigation_repository.get_investigation(
            investigation_id
        )
    )

    if investigation is None:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found.",
        )

    return investigation


# ==========================================================
# LIST RECENT INVESTIGATIONS
# ==========================================================

@app.get("/investigations")
async def get_recent_investigations(
    limit: int = 10,
):

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 100.",
        )

    investigations = (
        await investigation_repository.get_recent_investigations(
            limit=limit
        )
    )

    return {
        "count": len(investigations),
        "investigations": investigations,
    }


# ==========================================================
# GET APPROVAL
# ==========================================================

@app.get("/investigations/{investigation_id}/approval")
async def get_investigation_approval(
    investigation_id: int,
):

    investigation = (
        await investigation_repository.get_investigation(
            investigation_id
        )
    )

    if investigation is None:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found.",
        )

    approval = await approval_repository.get_approval(
        investigation_id
    )

    if approval is None:
        raise HTTPException(
            status_code=404,
            detail="No approval decision found.",
        )

    return approval


# ==========================================================
# SHARED APPROVAL DECISION HANDLER
# ==========================================================

async def submit_approval_decision(
    investigation_id: int,
    request: ApprovalRequest,
    decision: str,
):

    investigation = (
        await investigation_repository.get_investigation(
            investigation_id
        )
    )

    if investigation is None:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found.",
        )

    current_status = investigation["investigation"]["status"]

    if current_status != "awaiting_approval":
        raise HTTPException(
            status_code=409,
            detail=(
                "Investigation has already received a decision "
                "or is not awaiting approval."
            ),
        )

    try:

        return await approval_repository.submit_decision(
            investigation_id=investigation_id,
            decision=decision,
            reviewer=request.reviewer,
            comments=request.comments,
        )

    except ValueError as error:

        message = str(error)

        if "Only investigations awaiting approval" in message:
            raise HTTPException(
                status_code=409,
                detail=message,
            ) from error

        if "not found" in message.lower():
            raise HTTPException(
                status_code=404,
                detail=message,
            ) from error

        raise HTTPException(
            status_code=400,
            detail=message,
        ) from error


# ==========================================================
# APPROVE INVESTIGATION
# ==========================================================

@app.post("/investigations/{investigation_id}/approve")
async def approve_investigation(
    investigation_id: int,
    request: ApprovalRequest,
):

    return await submit_approval_decision(
        investigation_id=investigation_id,
        request=request,
        decision="approved",
    )


# ==========================================================
# REJECT INVESTIGATION
# ==========================================================

@app.post("/investigations/{investigation_id}/reject")
async def reject_investigation(
    investigation_id: int,
    request: ApprovalRequest,
):

    return await submit_approval_decision(
        investigation_id=investigation_id,
        request=request,
        decision="rejected",
    )

# ==========================================================
# GET INDUSTRIAL FACILITIES
# ==========================================================

@app.get("/facilities")
async def get_facilities():
    """
    Return all industrial facilities and their locations.
    """

    facilities = []

    for facility in INDUSTRIAL_FACILITIES:
        facilities.append({
            "facility_id": facility.facility_id,
            "facility_name": facility.facility_name,
            "industry_type": facility.industry_type,
            "latitude": facility.latitude,
            "longitude": facility.longitude,
            "permitted_pm25": facility.permitted_pm25,
            "permitted_so2": facility.permitted_so2,
            "data_source": "synthetic_demo_dataset",
        })

    return {
        "count": len(facilities),
        "facilities": facilities,
    }



# ==========================================================
# AGGREGATE MCP TOOL METRICS
# ==========================================================

@app.get("/metrics/mcp")
async def get_aggregate_mcp_metrics():
    """
    Return aggregate MCP tool performance metrics across
    all stored investigations.
    """

    try:
        return await investigation_repository.get_aggregate_mcp_metrics()

    except Exception as error:
        logger.exception("Could not retrieve aggregate MCP metrics")

        raise HTTPException(
            status_code=500,
            detail="Could not retrieve MCP metrics.",
        ) from error
