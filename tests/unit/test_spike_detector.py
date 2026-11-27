from src.agents.spike_detector import SpikeDetector
from src.data.sample_data import AIR_QUALITY_READINGS


def test_detect_exceedance():

    detector = SpikeDetector()

    reading = AIR_QUALITY_READINGS[2]

    result = detector.detect(reading)

    assert result["is_exceedance"] is True
    assert result["station_id"] == "ST-001"
    assert result["exceedance_count"] > 0


def test_no_exceedance():

    detector = SpikeDetector()

    reading = AIR_QUALITY_READINGS[0]

    result = detector.detect(reading)

    assert result["is_exceedance"] is False
    assert result["exceedance_count"] == 0