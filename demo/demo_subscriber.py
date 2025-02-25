import logging
import sys
import time

from vdv736.subscriber import Subscriber

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")

def on_delivery(delivery):
    print('Delivery callback called...')

with Subscriber('PY_TEST_SUBSCRIBER', './demo/demo_participants.yaml') as subscriber:

    if len(sys.argv) > 1 and sys.argv[1] == 'ps':
    
        time.sleep(15)
        sid = subscriber.subscribe('PY_TEST_PUBLISHER')
        time.sleep(10)
        subscriber.status(sid)
        time.sleep(10)
        subscriber.unsubscribe(sid)

        subscriber.set_callbacks(on_delivery)
        sid = subscriber.subscribe('PY_TEST_PUBLISHER')

        while True:
            time.sleep(30)
            subscriber.status()

    else:

        time.sleep(25)
        subscriber.request('PY_TEST_PUBLISHER')
        print(subscriber.get_situations())

        while True:
            pass