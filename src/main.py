
import asyncio
import logging
import time

from src.core.logging_config import setup_logging
from src.orchestration.supervisor import Supervisor


logger = logging.getLogger(__name__)


async def main():

    setup_logging()

    start_time = time.perf_counter()

    print("\n" + "=" * 60)
    print("INDUSTRIAL EMISSION EXCEEDANCE")
    print("SOURCE ATTRIBUTION INVESTIGATION")
    print("=" * 60)

    logger.info("Investigation application started.")

    supervisor = Supervisor(
        station_latitude=13.0800,
        station_longitude=80.2600,
    )

    print("\nConnecting to environmental MCP servers...\n")

    try:
        result = await supervisor.run_investigation_with_mcp(
            station_id="ST-001",
        )

    except Exception:
        logger.exception("Investigation failed unexpectedly.")
        raise

    total_time = time.perf_counter() - start_time

    logger.info(
        "Investigation finished with status=%s in %.2f seconds",
        result.get("status"),
        total_time,
    )

    print("\nINVESTIGATION STATUS:", result["status"])

    if result["status"] != "success":
        print("Message:", result.get("message", "Investigation incomplete."))
        print(f"Execution time: {total_time:.2f} seconds")
        return

    exceedance = result["exceedance_result"]

    print("\n--- AIR QUALITY ANALYSIS ---")
    print("Station:", result["station_id"])
    print("Timestamp:", result["investigation_timestamp"])
    print("Exceedances:", exceedance["exceedance_count"])

    for item in exceedance["exceedances"]:
        print(
            f'{item["pollutant"].upper()}: '
            f'{item["measured_value"]} '
            f'(threshold: {item["threshold"]})'
        )

    print("\n--- WIND CONDITIONS ---")
    print("Wind speed:", result["wind_reading"]["wind_speed"])
    print("Wind direction:", result["wind_reading"]["wind_direction"])

    print("\n--- FACILITY SCREENING ---")

    for candidate in result["screened_candidates"]:
        print(
            f'{candidate["facility_name"]} | '
            f'Distance: {candidate["distance_km"]} km | '
            f'Wind aligned: {candidate["is_directionally_aligned"]}'
        )

    print("\n--- INSPECTION PRIORITIES ---")

    for recommendation in result["investigation_plan"]["recommendations"]:
        print(
            f'{recommendation["facility_name"]} | '
            f'Score: {recommendation["priority_score"]} | '
            f'Priority: {recommendation["priority_level"].upper()}'
        )

    print("\n--- DECISION NOTE ---")
    print(result["investigation_plan"]["decision_note"])

    print("\nDATA SOURCE:", result.get("data_source"))

    print("\n--- LLM INTERPRETATION STATUS ---")
    print(result.get("llm_interpretation_status", "not available"))

    if result.get("llm_interpretation") is not None:

        print("\n--- LLM INVESTIGATION INTERPRETATION ---")

        for field, value in result["llm_interpretation"].items():
            print(f"\n{field.upper()}:")

            if isinstance(value, list):
                for item in value:
                    print("-", item)
            else:
                print(value)

    else:
        print("\nLLM interpretation was not accepted.")

        if "llm_validation" in result:
            print("Validation errors:")

            for error in result["llm_validation"]["errors"]:
                print("-", error)

        if "llm_error" in result:
            print("LLM error:", result["llm_error"])

        print(result.get("llm_fallback_message", ""))

    if "mcp_cleanup_warning" in result:
        print("\nMCP cleanup warning:", result["mcp_cleanup_warning"])

    print("\n--- MCP PERFORMANCE METRICS ---")

    metrics = result.get("mcp_metrics", {})

    print("Total calls:", metrics.get("total_calls", 0))
    print("Total attempts:", metrics.get("total_attempts", 0))
    print("Successful calls:", metrics.get("successful_calls", 0))
    print("Failed calls:", metrics.get("failed_calls", 0))
    print("Retries:", metrics.get("retries", 0))

    print(
        "Total attempt duration:",
        f'{metrics.get("total_attempt_duration_seconds", 0):.4f} seconds'
    )

    print("\nIndividual MCP Tool Metrics:")

    for tool, tool_metrics in metrics.get("tools", {}).items():

        print(f"\n{tool}")

        print("  Calls:", tool_metrics["calls"])
        print("  Successes:", tool_metrics["successes"])
        print("  Failures:", tool_metrics["failures"])
        print("  Retries:", tool_metrics["retries"])

        print(
            "  Total duration:",
            f'{tool_metrics["total_attempt_duration_seconds"]:.4f} seconds'
        )
    
    print(f"\nTOTAL EXECUTION TIME: {total_time:.2f} seconds")

    print("\n" + "=" * 60)
    print("INVESTIGATION COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
