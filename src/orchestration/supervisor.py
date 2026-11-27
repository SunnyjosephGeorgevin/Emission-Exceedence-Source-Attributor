
import logging
import time

from src.services.recovery_service import RecoveryService

from src.agents.spike_detector import SpikeDetector
from src.agents.wind_backtracker import WindBacktracker
from src.agents.facility_profiler import FacilityProfiler
from src.agents.inspection_planner import InspectionPlanner
from src.agents.llm_interpreter import LLMInterpreter
from src.agents.interpretation_validator import InterpretationValidator

from src.services.mcp_data_provider import MCPDataProvider

from src.data.models import (
    AirQualityReading,
    WindReading,
    IndustrialFacility,
)

from src.database.repository import InvestigationRepository
from src.database.checkpoint_repository import CheckpointRepository


logger = logging.getLogger(__name__)


class Supervisor:

    def __init__(
        self,
        station_latitude: float,
        station_longitude: float,
    ):

        if not -90 <= station_latitude <= 90:
            raise ValueError("Invalid station latitude.")

        if not -180 <= station_longitude <= 180:
            raise ValueError("Invalid station longitude.")

        self.station_latitude = station_latitude
        self.station_longitude = station_longitude

        self.spike_detector = SpikeDetector()

        self.wind_backtracker = WindBacktracker(
            station_latitude=station_latitude,
            station_longitude=station_longitude,
        )

        self.facility_profiler = FacilityProfiler()
        self.inspection_planner = InspectionPlanner()
        self.llm_interpreter = LLMInterpreter()
        self.interpretation_validator = InterpretationValidator()

        self.investigation_repository = InvestigationRepository()
        self.checkpoint_repository = CheckpointRepository()
        self.recovery_service = RecoveryService()

    # ==========================================================
    # CHECKPOINT COORDINATES
    # ==========================================================

    def _station_checkpoint_data(self) -> dict:

        return {
            "station_latitude": self.station_latitude,
            "station_longitude": self.station_longitude,
        }

    # ==========================================================
    # AMBIENT READING SERIALIZATION
    # ==========================================================

    def _serialize_ambient_reading(
        self,
        reading: AirQualityReading,
    ) -> dict:

        """
        Preserve every pollutant measurement, including
        measurements that do not exceed configured thresholds.
        """

        return {
            "station_id": reading.station_id,
            "timestamp": reading.timestamp.isoformat(),
            "pm25": reading.pm25,
            "pm10": reading.pm10,
            "so2": reading.so2,
            "nox": reading.nox,
        }

    # ==========================================================
    # PYTHON INVESTIGATION
    # ==========================================================

    def run_investigation(
        self,
        air_quality_readings: list,
        wind_readings: list,
        facilities: list,
    ) -> dict:

        print("\n[4/6] Running Python investigation...", flush=True)

        if not air_quality_readings:
            return {
                "status": "failed",
                "message": "No air-quality readings available.",
            }

        latest_reading = max(
            air_quality_readings,
            key=lambda reading: reading.timestamp,
        )

        # Preserve the complete ambient reading.
        ambient_reading = self._serialize_ambient_reading(
            latest_reading
        )

        exceedance_result = self.spike_detector.detect(
            latest_reading
        )

        if not exceedance_result["is_exceedance"]:

            return {
                "status": "no_exceedance",
                "station_id": latest_reading.station_id,
                "investigation_timestamp": (
                    latest_reading.timestamp.isoformat()
                ),
                "ambient_reading": ambient_reading,
                "exceedance_result": exceedance_result,
                "recommendations": [],
                "data_source": "synthetic_demo_dataset",
            }

        matching_wind = next(
            (
                wind for wind in wind_readings
                if wind.timestamp == latest_reading.timestamp
            ),
            None,
        )

        if matching_wind is None:

            return {
                "status": "failed",
                "station_id": latest_reading.station_id,
                "ambient_reading": ambient_reading,
                "message": "No matching wind reading found.",
                "exceedance_result": exceedance_result,
            }

        candidates = self.wind_backtracker.investigate(
            wind=matching_wind,
            facilities=facilities,
        )

        facility_profiles = self.facility_profiler.profile_all(
            facilities
        )

        investigation_plan = self.inspection_planner.generate_plan(
            exceedance_result=exceedance_result,
            candidates=candidates,
            facility_profiles=facility_profiles,
        )

        print(
            "[4/6] Python investigation completed.",
            flush=True,
        )

        return {
            "status": "success",
            "station_id": latest_reading.station_id,
            "investigation_timestamp": (
                latest_reading.timestamp.isoformat()
            ),

            # Complete original monitoring measurements.
            "ambient_reading": ambient_reading,

            "exceedance_result": exceedance_result,

            "wind_reading": {
                "wind_speed": matching_wind.wind_speed,
                "wind_direction": matching_wind.wind_direction,
            },

            "screened_candidates": candidates,
            "facility_profiles": facility_profiles,
            "investigation_plan": investigation_plan,

            "data_source": "synthetic_demo_dataset",
        }

    # ==========================================================
    # LLM INTERPRETATION
    # ==========================================================

    async def _run_llm_interpretation(
        self,
        result: dict,
    ) -> dict:

        try:

            interpretation = await self.llm_interpreter.interpret(
                result
            )

            interpretation_data = interpretation.model_dump()

            validation_result = self.interpretation_validator.validate(
                interpretation=interpretation_data,
                investigation_result=result,
            )

            result["llm_validation"] = validation_result

            if validation_result["is_valid"]:

                result["llm_interpretation"] = interpretation_data

                result["llm_interpretation_status"] = (
                    "passed_basic_checks"
                )

            else:

                result["llm_interpretation"] = None

                result["llm_interpretation_status"] = "rejected"

                result["llm_fallback_message"] = (
                    "LLM interpretation failed factual validation. "
                    "The deterministic Python investigation remains "
                    "available and authoritative."
                )

        except Exception as llm_error:

            logger.exception(
                "LLM interpretation or validation failed."
            )

            result["llm_interpretation"] = None
            result["llm_interpretation_status"] = "unavailable"
            result["llm_error"] = str(llm_error)

            result["llm_fallback_message"] = (
                "LLM interpretation could not be generated. "
                "The deterministic Python investigation remains "
                "available and authoritative."
            )

        return result

    # ==========================================================
    # NORMAL INVESTIGATION WORKFLOW
    # ==========================================================

    async def run_investigation_with_mcp(
        self,
        station_id: str,
        investigation_id: int | None = None,
    ) -> dict:

        if investigation_id is not None:

            existing = await self.investigation_repository.get_investigation(
                investigation_id
            )

            if existing is None:
                raise ValueError(
                    f"Investigation {investigation_id} not found."
                )

            investigation = existing["investigation"]

            if investigation["station_id"] != station_id:
                raise ValueError(
                    "Investigation station ID does not match the request."
                )

            if investigation["status"] != "pending":
                raise ValueError(
                    "Only pending investigations can be started."
                )

            stored_latitude = investigation.get("station_latitude")
            stored_longitude = investigation.get("station_longitude")

            if (
                stored_latitude is not None
                and stored_longitude is not None
                and (
                    stored_latitude != self.station_latitude
                    or stored_longitude != self.station_longitude
                )
            ):
                raise ValueError(
                    "Station coordinates do not match the saved investigation."
                )

        provider = MCPDataProvider()
        result = None
        total_start = time.perf_counter()

        try:

            if investigation_id is None:

                investigation_id = (
                    await self.investigation_repository.create_investigation(
                        station_id=station_id,
                        status="pending",
                        current_stage="pending",
                        station_latitude=self.station_latitude,
                        station_longitude=self.station_longitude,
                    )
                )

                logger.info(
                    "Investigation created. ID: %s",
                    investigation_id,
                )

            else:

                logger.info(
                    "Using API-created investigation. ID: %s",
                    investigation_id,
                )

            print(
                f"\nInvestigation ID: {investigation_id}",
                flush=True,
            )

            await self.investigation_repository.update_investigation(
                investigation_id=investigation_id,
                status="running",
                current_stage="connecting_to_mcp",
            )

            # Connect MCP servers.
            print(
                "\n[1/6] Connecting to MCP servers...",
                flush=True,
            )

            stage_start = time.perf_counter()

            await provider.connect_all()

            connection_duration = time.perf_counter() - stage_start

            logger.info(
                "MCP connection completed in %.4f seconds",
                connection_duration,
            )

            print(
                f"[2/6] MCP connections established "
                f"({connection_duration:.2f}s).",
                flush=True,
            )

            # Retrieve environmental data.
            print(
                "\n[3/6] Retrieving environmental data...",
                flush=True,
            )

            stage_start = time.perf_counter()

            (
                air_quality_readings,
                wind_readings,
                facilities,
            ) = await provider.fetch_environmental_data(station_id)

            retrieval_duration = time.perf_counter() - stage_start

            logger.info(
                "Environmental retrieval completed in %.4f seconds",
                retrieval_duration,
            )

            # Save checkpoint with station coordinates.
            checkpoint_state = {
                **self._station_checkpoint_data(),

                "air_quality_readings": [
                    item.model_dump(mode="json")
                    for item in air_quality_readings
                ],

                "wind_readings": [
                    item.model_dump(mode="json")
                    for item in wind_readings
                ],

                "facilities": [
                    item.model_dump(mode="json")
                    for item in facilities
                ],
            }

            await self.checkpoint_repository.save_checkpoint(
                investigation_id=investigation_id,
                stage="data_retrieved",
                state=checkpoint_state,
            )

            # Run deterministic investigation.
            result = self.run_investigation(
                air_quality_readings=air_quality_readings,
                wind_readings=wind_readings,
                facilities=facilities,
            )

            result["investigation_id"] = investigation_id

            if result["status"] != "success":
                return result

            await self.checkpoint_repository.save_checkpoint(
                investigation_id=investigation_id,
                stage="python_investigation_completed",
                state={
                    **self._station_checkpoint_data(),
                    "investigation_result": result,
                },
            )

            # LLM interpretation.
            stage_start = time.perf_counter()

            result = await self._run_llm_interpretation(result)

            llm_duration = time.perf_counter() - stage_start

            logger.info(
                "LLM processing completed in %.4f seconds",
                llm_duration,
            )

            # Save complete checkpoint.
            await self.checkpoint_repository.save_checkpoint(
                investigation_id=investigation_id,
                stage="llm_interpretation_completed",
                state={
                    **self._station_checkpoint_data(),
                    "investigation_result": result,
                },
            )

            result["review_status"] = "awaiting_approval"

            total_duration = time.perf_counter() - total_start

            print(
                f"\nTotal Supervisor execution time: "
                f"{total_duration:.2f}s",
                flush=True,
            )

            return result

        except Exception as error:

            logger.exception(
                "Supervisor investigation failed."
            )

            result = {
                "status": "failed",
                "station_id": station_id,
                "message": str(error),
            }

            if investigation_id is not None:
                result["investigation_id"] = investigation_id

            return result

        finally:

            if result is not None and investigation_id is not None:

                result["mcp_metrics"] = provider.get_metrics()

                result["supervisor_execution_seconds"] = round(
                    time.perf_counter() - total_start,
                    4,
                )

                if result["status"] == "failed":
                    final_status = "failed"
                    final_stage = "failed"

                elif result["status"] == "no_exceedance":
                    final_status = "completed"
                    final_stage = "completed"

                else:
                    final_status = "awaiting_approval"
                    final_stage = "awaiting_approval"

                try:

                    await self.investigation_repository.update_investigation(
                        investigation_id=investigation_id,
                        status=final_status,
                        current_stage=final_stage,
                        execution_seconds=result[
                            "supervisor_execution_seconds"
                        ],
                        mcp_metrics=provider.get_metrics(),
                        result_data=result,
                        error_message=(
                            result.get("message")
                            if final_status == "failed"
                            else None
                        ),
                    )

                except Exception:

                    logger.exception(
                        "Failed to persist final investigation state."
                    )

                    result["database_persistence_warning"] = (
                        "Final investigation state could not be saved."
                    )

            try:

                await provider.close()

            except Exception as close_error:

                logger.exception(
                    "MCP connection cleanup failed."
                )

                if result is not None:
                    result["mcp_cleanup_warning"] = str(close_error)

    # ==========================================================
    # INVESTIGATION RECOVERY
    # ==========================================================

    async def resume_investigation(
        self,
        investigation_id: int,
    ) -> dict:

        total_start = time.perf_counter()
        recovery = None

        claimed = await self.checkpoint_repository.claim_recovery(
            investigation_id
        )

        if not claimed:

            return {
                "status": "recovery_claim_rejected",
                "investigation_id": investigation_id,
                "message": (
                    "Investigation is not available for recovery."
                ),
            }

        try:

            recovery = await self.recovery_service.prepare_recovery(
                investigation_id
            )

            action = recovery["next_action"]
            state = recovery["reconstructed_state"]

            # Restore station coordinates.
            latitude = state.get("station_latitude")
            longitude = state.get("station_longitude")

            if latitude is None:
                latitude = self.station_latitude

            if longitude is None:
                longitude = self.station_longitude

            if latitude is None or longitude is None:
                raise ValueError(
                    "Station coordinates are unavailable. "
                    "Cannot safely resume this investigation."
                )

            if (
                state.get("station_latitude") is not None
                and latitude != self.station_latitude
            ):
                raise ValueError(
                    "Recovery latitude does not match "
                    "the Supervisor configuration."
                )

            if (
                state.get("station_longitude") is not None
                and longitude != self.station_longitude
            ):
                raise ValueError(
                    "Recovery longitude does not match "
                    "the Supervisor configuration."
                )

            result = None

            # Resume deterministic investigation.
            if action == "resume_python_investigation":

                air_quality_readings = [
                    AirQualityReading(**item)
                    for item in state["air_quality_readings"]
                ]

                wind_readings = [
                    WindReading(**item)
                    for item in state["wind_readings"]
                ]

                facilities = [
                    IndustrialFacility(**item)
                    for item in state["facilities"]
                ]

                result = self.run_investigation(
                    air_quality_readings=air_quality_readings,
                    wind_readings=wind_readings,
                    facilities=facilities,
                )

                result["investigation_id"] = investigation_id

                if result["status"] == "success":

                    await self.checkpoint_repository.save_checkpoint(
                        investigation_id=investigation_id,
                        stage="python_investigation_completed",
                        state={
                            **self._station_checkpoint_data(),
                            "investigation_result": result,
                        },
                    )

            # Resume LLM interpretation.
            elif action == "resume_llm_interpretation":

                result = state["investigation_result"]

            # Restore completed interpretation.
            elif action == "finalize_for_human_approval":

                result = state["investigation_result"]

            else:

                raise ValueError(
                    f"Unsupported recovery action: {action}"
                )

            # Execute LLM only if not already completed.
            if (
                action in {
                    "resume_python_investigation",
                    "resume_llm_interpretation",
                }
                and result["status"] == "success"
            ):

                result = await self._run_llm_interpretation(result)

                await self.checkpoint_repository.save_checkpoint(
                    investigation_id=investigation_id,
                    stage="llm_interpretation_completed",
                    state={
                        **self._station_checkpoint_data(),
                        "investigation_result": result,
                    },
                )

            if result["status"] == "failed":

                final_status = "failed"
                final_stage = "failed"

            elif result["status"] == "no_exceedance":

                final_status = "completed"
                final_stage = "completed"

            else:

                final_status = "awaiting_approval"
                final_stage = "awaiting_approval"

                result["review_status"] = "awaiting_approval"

            execution_seconds = round(
                time.perf_counter() - total_start,
                4,
            )

            result["supervisor_execution_seconds"] = execution_seconds

            await self.investigation_repository.update_investigation(
                investigation_id=investigation_id,
                status=final_status,
                current_stage=final_stage,
                execution_seconds=execution_seconds,
                result_data=result,
                error_message=(
                    result.get("message")
                    if final_status == "failed"
                    else None
                ),
            )

            logger.info(
                "Investigation %s recovered successfully.",
                investigation_id,
            )

            return result

        except Exception as error:

            logger.exception(
                "Recovery failed for investigation %s",
                investigation_id,
            )

            try:

                await self.checkpoint_repository.release_recovery(
                    investigation_id
                )

            except Exception:

                logger.exception(
                    "Failed to release recovery claim."
                )

            return {
                "status": "recovery_failed",
                "investigation_id": investigation_id,
                "station_id": (
                    recovery["station_id"]
                    if recovery is not None
                    else None
                ),
                "message": str(error),
                "failure_stage": (
                    recovery["recovery_stage"]
                    if recovery is not None
                    else "recovery_preparation"
                ),
            }
