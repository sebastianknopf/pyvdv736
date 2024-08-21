import logging
import sys
import time

from vdv736.subscriber import Subscriber

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")

with Subscriber('PY_TEST_SUBSCRIBER', 'demo_participants.yaml') as subscriber:

    if len(sys.argv) > 1 and sys.argv[1] == 'ps':
    
        time.sleep(15)
        sid = subscriber.subscribe('PY_TEST_PUBLISHER')
        time.sleep(10)
        subscriber.status(sid)
        time.sleep(10)
        subscriber.unsubscribe(sid)
        sid = subscriber.subscribe('PY_TEST_PUBLISHER')

        while True:
            time.sleep(60)
            subscriber.status()

    else:

        time.sleep(25)
        subscriber.request('PY_TEST_PUBLISHER')
        print(subscriber.get_situations())

        while True:
            pass