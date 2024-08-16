import logging
import sys
import time

from vdv736.subscriber import SubscriberController
from vdv736.subscriber import SubscriberEndpoint

logger = logging.getLogger()
logger.setLevel(logging.INFO)

if len(sys.argv) > 1 and sys.argv[1] == 'controller':
    controller = SubscriberController()
    subscription_id = controller.subscribe('http://127.0.0.1', 9091, 'PY_TEST_SUBSCRIBER')

    time.sleep(10)

    controller.unsubscribe(subscription_id)

    while True:
        controller.get_situations()
        time.sleep(60)
else:
    endpoint = SubscriberEndpoint().create_endpoint()