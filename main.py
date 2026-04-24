import requests
import random
import time

URL = "http://127.0.0.1:5000/event"

plates = ["IS-01-ABC", "IS-99-XYZ", "B-123-AAA", "IS-77-NEW"]

while True:
    plate = random.choice(plates)
    speed = random.randint(40, 120)
    limit = 60

    if speed > limit:
        requests.post(URL, json={
            "plate": plate,
            "speed": speed,
            "limit": limit
        })
        print("Sent:", plate, speed)
    else:
        print(f"{plate} OK ({speed})")

    time.sleep(5)