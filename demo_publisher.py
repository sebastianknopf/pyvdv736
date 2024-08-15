import logging
import sys
import time

from vdv736.publisher import PublisherController
from vdv736.publisher import PublisherEndpoint

logger = logging.getLogger()
logger.setLevel(logging.INFO)

if len(sys.argv) > 1 and sys.argv[1] == 'controller':
    controller = PublisherController()

    while True:
        controller.publish()
        time.sleep(300)
else:
    endpoint = PublisherEndpoint().create_endpoint()