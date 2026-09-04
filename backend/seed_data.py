"""Generate a realistic set of historical readings so the dashboard has data.

Also injects a few deliberate anomalies so the ML detection and alerts UI are
demonstrable on first run.

Usage:  python seed_data.py
"""
import math
import random
from datetime import datetime, timedelta, timezone

from database import init_db, SessionLocal
import models

random.seed(42)

# A few plausible deployment sites across a city.
LOCATIONS = [
    {"device_id": "water-node-01", "name": "Sanganer River Gauge",
     "lat": 26.8128, "lon": 75.7868, "base_tds": 420.0},
    {"device_id": "water-node-02", "name": "Amanishah Nala",
     "lat": 26.9180, "lon": 75.7860, "base_tds": 680.0},
    {"device_id": "water-node-03", "name": "Jhalana Reservoir",
     "lat": 26.8600, "lon": 75.8000, "base_tds": 260.0},
]

# Realistic baseline ranges per parameter (healthy water).
PARAM_BASE = {
    "ph": (7.0, 7.8),
    "temperature": (22.0, 30.0),
    "turbidity": (1.0, 6.0),
    "dissolved_oxygen": (5.5, 8.0),
    "conductivity": (400.0, 900.0),
    "tds": (250.0, 500.0),
}

# Anomaly "event" definitions injected at specific timestamps.
# Each is (minutes_ago, parameter, offset).
ANOMALY_EVENTS = [
    (40,  "ph",               -1.8),   # sudden acid spike
    (95,  "dissolved_oxygen", -3.5),   # oxygen crash -> fish-kill risk
    (150, "turbidity",        +45.0),  # sediment / sewage inflow
    (210, "conductivity",     +1800.0),# industrial discharge
    (260, "tds",              +1500.0),
]


def base_value(param, base_mid, t):
    """A slowly varying healthy value (sinusoidal drift + small noise)."""
    lo, hi = PARAM_BASE[param]
    mid = (lo + hi) / 2
    amp = (hi - lo) / 2
    wave = mid + amp * math.sin(t / (60 * 12) + hash(param) % 7)  # ~12h period
    return wave + random.uniform(-0.05, 0.05) * amp


def main():
    init_db()
    db = SessionLocal()

    # Idempotent: wipe existing data so re-seeding is clean.
    db.query(models.Alert).delete()
    db.query(models.SensorReading).delete()
    db.query(models.Device).delete()

    now = datetime.now(timezone.utc)
    total = 0
    for loc in LOCATIONS:
        device_id = loc["device_id"]
        tds_mid = loc["base_tds"]
        # 72 hours of readings at 5-minute intervals.
        for minutes_ago in range(72 * 60, -1, -5):
            t = now - timedelta(minutes=minutes_ago)
            t_val = minutes_ago

            # Healthy base values.
            ph = base_value("ph", None, t_val)
            temperature = base_value("temperature", None, t_val)
            turbidity = base_value("turbidity", None, t_val)
            dissolved_oxygen = base_value("dissolved_oxygen", None, t_val)
            conductivity = tds_mid * 2.1 + random.uniform(-30, 30)
            tds = tds_mid + random.uniform(-25, 25)

            # Apply anomaly offsets for events that fall within this device's window.
            for (ago, param, offset) in ANOMALY_EVENTS:
                if ago <= minutes_ago <= ago + 8 and device_id == "water-node-01":
                    if param == "ph":
                        ph += offset
                    elif param == "temperature":
                        temperature += offset
                    elif param == "turbidity":
                        turbidity += offset
                    elif param == "dissolved_oxygen":
                        dissolved_oxygen += offset
                    elif param == "conductivity":
                        conductivity += offset
                    elif param == "tds":
                        tds += offset

            reading = models.SensorReading(
                device_id=device_id,
                ph=round(ph, 2),
                temperature=round(temperature, 2),
                turbidity=round(turbidity, 2),
                dissolved_oxygen=round(dissolved_oxygen, 2),
                conductivity=round(conductivity, 2),
                tds=round(tds, 2),
                latitude=loc["lat"],
                longitude=loc["lon"],
                location_name=loc["name"],
                created_at=t,
            )
            db.add(reading)
            total += 1

        # Register the device as online.
        db.add(models.Device(
            device_id=device_id,
            name=loc["name"],
            location_name=loc["name"],
            latitude=loc["lat"],
            longitude=loc["lon"],
            status="online",
            last_seen=now,
        ))

    db.commit()
    print(f"Seeded {total} readings across {len(LOCATIONS)} devices.")


if __name__ == "__main__":
    main()
