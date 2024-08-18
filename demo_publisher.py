import logging
import uuid
import time

from vdv736.model import PublicTransportSituation
from vdv736.publisher import Publisher

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")

with Publisher('PY_TEST_PUBLISHER', 'demo_participants.yaml') as publisher:
    
    time.sleep(5)

    publisher.publish_situation(PublicTransportSituation.create(uuid.uuid4()))

    time.sleep(15)

    publisher.publish_situation(PublicTransportSituation.create(uuid.uuid4()))

    time.sleep(20)

    while True:
        pass