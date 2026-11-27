import math

from src.data.models import (
    WindReading,
    IndustrialFacility,
)


class WindBacktracker:

    def __init__(
        self,
        station_latitude: float,
        station_longitude: float,
        direction_tolerance: float = 45.0,
        max_distance_km: float = 20.0,
    ):
        self.station_latitude = station_latitude
        self.station_longitude = station_longitude
        self.direction_tolerance = direction_tolerance
        self.max_distance_km = max_distance_km

    def calculate_distance(self, facility):
        """Calculate distance using the Haversine formula."""

        radius = 6371.0

        lat1 = math.radians(self.station_latitude)
        lat2 = math.radians(facility.latitude)

        delta_lat = math.radians(
            facility.latitude - self.station_latitude
        )
        delta_lon = math.radians(
            facility.longitude - self.station_longitude
        )

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1)
            * math.cos(lat2)
            * math.sin(delta_lon / 2) ** 2
        )

        c = 2 * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a),
        )

        return radius * c

    def calculate_bearing(self, facility):
        """Calculate bearing from monitoring station to facility."""

        lat1 = math.radians(self.station_latitude)
        lat2 = math.radians(facility.latitude)

        delta_lon = math.radians(
            facility.longitude - self.station_longitude
        )

        x = math.sin(delta_lon) * math.cos(lat2)

        y = (
            math.cos(lat1) * math.sin(lat2)
            - math.sin(lat1)
            * math.cos(lat2)
            * math.cos(delta_lon)
        )

        bearing = math.degrees(math.atan2(x, y))

        return (bearing + 360) % 360

    def investigate(
        self,
        wind: WindReading,
        facilities: list[IndustrialFacility],
    ) -> list[dict]:

        candidates = []

        for facility in facilities:

            distance = self.calculate_distance(facility)

            if distance > self.max_distance_km:
                continue

            bearing = self.calculate_bearing(facility)

            # Wind comes FROM this direction.
            # A facility is potentially upwind when its
            # bearing from the station is near this direction.
            difference = abs(
                (bearing - wind.wind_direction + 180) % 360 - 180
            )

            is_directionally_aligned = (
                difference <= self.direction_tolerance
            )

            candidates.append({
                "facility_id": facility.facility_id,
                "facility_name": facility.facility_name,
                "distance_km": round(distance, 2),
                "bearing_degrees": round(bearing, 2),
                "wind_direction": wind.wind_direction,
                "wind_speed": wind.wind_speed,
                "direction_difference": round(difference, 2),
                "is_directionally_aligned": is_directionally_aligned,
            })

        return candidates