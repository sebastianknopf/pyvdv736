import time
import sys

from vdv736.subscriber import SubscriberController
from vdv736.subscriber import SubscriberEndpoint

if len(sys.argv) > 1 and sys.argv[1] == 'controller':
    controller = SubscriberController()
    controller.subscribe('http://127.0.0.1', 8080, 'PY_TEST_SUBSCRIBER')

    while True:
        controller.get_situations()
        time.sleep(2)
else:
    endpoint = SubscriberEndpoint().create_endpoint()