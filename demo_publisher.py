import logging
import sys
import time

from vdv736.publisher import Publisher
from vdv736.publisher import PublisherEndpoint

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")

with Publisher('PY_TEST_PUBLISHER') as publisher:
    
    time.sleep(5)

    publisher.publish()

    time.sleep(15)

    publisher.publish()

    time.sleep(20)