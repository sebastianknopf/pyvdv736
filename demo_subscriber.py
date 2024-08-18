import logging
import sys
import time

from vdv736.subscriber import Subscriber

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")

with Subscriber() as subscriber:

    time.sleep(15)
    
    sid = subscriber.subscribe('http://127.0.0.1', 9091, 'PY_TEST_SUBSCRIBER')

    time.sleep(10)

    subscriber.status(sid)

    time.sleep(10)

    subscriber.unsubscribe(sid)

    while True:
        pass