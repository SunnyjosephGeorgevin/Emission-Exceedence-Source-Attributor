from src.core.thresholds import AMBIENT_THRESHOLDS
from src.data.models import AirQualityReading


class SpikeDetector:

    def detect(self, reading: AirQualityReading) -> dict:
        """
        Compare ambient pollution readings against
        configured thresholds.
        """

        exceedances = []

        pollutant_values = {
            "pm25": reading.pm25,
            "pm10": reading.pm10,
            "so2": reading.so2,
            "nox": reading.nox,
        }

        for pollutant, measured_value in pollutant_values.items():

            threshold = AMBIENT_THRESHOLDS[pollutant]

            if measured_value > threshold:

                exceedances.append({
                    "pollutant": pollutant,
                    "measured_value": measured_value,
                    "threshold": threshold,
                    "excess": round(
                        measured_value - threshold, 2
                    ),
                    "exceedance_ratio": round(
                        measured_value / threshold, 2
                    ),
                })

        return {
            "station_id": reading.station_id,
            "timestamp": reading.timestamp.isoformat(),
            "is_exceedance": len(exceedances) > 0,
            "exceedance_count": len(exceedances),
            "exceedances": exceedances,
        }