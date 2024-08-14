import sys

from vdv736.subscriber import SubscriberController
from vdv736.subscriber import SubscriberEndpoint

def subscriber_callback(**kwargs):
    for k, v in kwargs.items():
        print(f"{k}={v}")

if len(sys.argv) > 1 and sys.argv[1] == 'controller':
    controller = SubscriberController()
    controller.subscribe('http://127.0.0.1', 8080, 'PY_TEST_SUBSCRIBER')

    while True:
        pass
else:
    endpoint = SubscriberEndpoint(subscriber_callback).create_endpoint()