import logging
import sys
import time

from vdv736.subscriber import Subscriber
from vdv736.subscriber import SubscriberEndpoint

logger = logging.getLogger()
logger.setLevel(logging.INFO)

with Subscriber() as subscriber:

    sid = subscriber.subscribe('http://127.0.0.1', 9091, 'PY_TEST_SUBSCRIBER')

    time.sleep(10)

    subscriber.status(sid)

    time.sleep(10)

    subscriber.unsubscribe(sid)