import logging
import sys
import time

from vdv736.subscriber import Subscriber

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")

with Subscriber('PY_TEST_SUBSCRIBER', 'demo_participants.yaml') as subscriber:

    time.sleep(15)
    
    sid = subscriber.subscribe('PY_TEST_PUBLISHER')

    time.sleep(10)

    subscriber.status(sid)

    time.sleep(10)

    subscriber.unsubscribe(sid)

    while True:
        pass