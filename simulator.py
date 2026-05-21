import requests
import time
import random

# Change to your Azure URL after deployment
# While testing locally keep it as localhost
SERVER_URL = "https://smart-bus-tracker-w4pj.onrender.com"

ROUTE_STOPS = [
    {"name": "Kempegowda Bus Station", "lat": 12.9767, "lng": 77.5713},
    {"name": "Vidhana Soudha",         "lat": 12.9793, "lng": 77.5908},
    {"name": "MG Road",                "lat": 12.9753, "lng": 77.6069},
    {"name": "Trinity Circle",         "lat": 12.9724, "lng": 77.6197},
    {"name": "Ulsoor Lake",            "lat": 12.9833, "lng": 77.6272},
    {"name": "Indiranagar",            "lat": 12.9784, "lng": 77.6408},
    {"name": "Domlur",                 "lat": 12.9591, "lng": 77.6387},
    {"name": "Koramangala",            "lat": 12.9352, "lng": 77.6245},
]

STEPS_PER_SEGMENT = 20  # 20 updates between each stop (5s each = ~100s per segment)

def interpolate(start, end, t):
    """Return lat/lng at fraction t (0.0 → 1.0) between two stops."""
    lat = start["lat"] + (end["lat"] - start["lat"]) * t
    lng = start["lng"] + (end["lng"] - start["lng"]) * t
    # Tiny random jitter for realism
    lat += random.uniform(-0.0002, 0.0002)
    lng += random.uniform(-0.0002, 0.0002)
    return round(lat, 6), round(lng, 6)
# Wake up server
try:
    requests.get(SERVER_URL, timeout=30)
    print("Server is awake!")
except:
    print("Waking up server...")

def simulate():
    step = 0
    total_segments = len(ROUTE_STOPS) - 1
    delay_counter = 0   # track consecutive delay steps

    print("=" * 50)
    print("  Smart Bus Tracker — Simulator Started")
    print("  Route: Majestic → Koramangala (Bengaluru)")
    print("=" * 50)

    while True:
        segment = (step // STEPS_PER_SEGMENT) % total_segments
        progress = (step % STEPS_PER_SEGMENT) / STEPS_PER_SEGMENT

        start_stop = ROUTE_STOPS[segment]
        end_stop   = ROUTE_STOPS[segment + 1]

        lat, lng = interpolate(start_stop, end_stop, progress)

        # Simulate delay: 15% base chance, clears after 3 steps
        if delay_counter > 0:
            delayed = True
            delay_counter -= 1
        elif random.random() < 0.15:
            delayed = True
            delay_counter = random.randint(2, 5)
        else:
            delayed = False

        # ETA = remaining segments × 5 min each (approx)
        remaining_segments = total_segments - segment - 1
        eta = int(remaining_segments * 5 + (1 - progress) * 5)

        data = {
            "bus_id":       "BUS-101",
            "route":        "Majestic \u2192 Koramangala",
            "lat":          lat,
            "lng":          lng,
            "current_stop": start_stop["name"],
            "next_stop":    end_stop["name"],
            "eta":          eta,
            "delayed":      delayed,
            "speed":        round(random.uniform(15, 45), 1),
            "status":       "Delayed" if delayed else "On Time",
            "timestamp":    time.strftime("%H:%M:%S"),
            "segment":      segment,
        }

        try:
            r = requests.post(f"{SERVER_URL}/update", json=data, timeout=30)
            status_icon = "⚠️ " if delayed else "✅"
            print(f"{status_icon} [{data['timestamp']}] {start_stop['name']} → {end_stop['name']} | ETA {eta} min | {data['speed']} km/h")
        except requests.exceptions.ConnectionError:
            print(f"[{time.strftime('%H:%M:%S')}] Cannot reach server at {SERVER_URL} — is app.py running?")
        except Exception as e:
            print(f"Error: {e}")

        step += 1
        time.sleep(5)

if __name__ == '__main__':
    simulate()
