import logging
import sys
import time

from vdv736.subscriber import Subscriber
from vdv736.delivery import SiriDelivery
from vdv736.sirixml import exists as sirixml_exists
from vdv736.sirixml import get_elements as sirixml_get_elements

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")

def on_delivery(delivery: SiriDelivery) -> None:
    print('Delivery callback called...')

    if sirixml_exists(delivery, 'Siri.ServiceDelivery.SituationExchangeDelivery.Situations'):
        pt_situations = sirixml_get_elements(delivery, 'Siri.ServiceDelivery.SituationExchangeDelivery.Situations.PtSituationElement')
        print(f"Found {len(pt_situations)} situations in this delivery")



with Subscriber('PY_TEST_SUBSCRIBER', './demo/demo_participants.yaml') as subscriber:

    if len(sys.argv) > 1 and sys.argv[1] == 'ps':

        subscriber.set_callbacks(on_delivery)

        time.sleep(15)
        sid = subscriber.subscribe('PY_TEST_PUBLISHER')
        time.sleep(10)
        subscriber.status(sid)
        time.sleep(10)
        subscriber.unsubscribe(sid)

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