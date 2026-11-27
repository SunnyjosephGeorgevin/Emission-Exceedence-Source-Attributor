from src.agents.facility_profiler import FacilityProfiler
from src.data.sample_data import INDUSTRIAL_FACILITIES


def test_profile_existing_facility():

    profiler = FacilityProfiler()

    result = profiler.profile(
        "FAC-001",
        INDUSTRIAL_FACILITIES,
    )

    assert result is not None
    assert result["facility_name"] == "Alpha Cement Works"
    assert result["profile_status"] == "success"


def test_profile_nonexistent_facility():

    profiler = FacilityProfiler()

    result = profiler.profile(
        "FAC-999",
        INDUSTRIAL_FACILITIES,
    )

    assert result is None


def test_profile_all_facilities():

    profiler = FacilityProfiler()

    results = profiler.profile_all(
        INDUSTRIAL_FACILITIES
    )

    assert len(results) == 3