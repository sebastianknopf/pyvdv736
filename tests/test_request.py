import unittest
import uuid

from vdv736.isotime import timestamp
from vdv736.model import Subscription
from vdv736.request import SiriRequest
from vdv736.request import SubscriptionRequest
from vdv736.request import SituationExchangeSubscriptionRequest


class SiriRequest_Test(unittest.TestCase):
    def test_SiriRequest(self):

        request = SiriRequest(
            'http://127.0.0.1', 
            8080
        )
        
        self.assertIsNotNone(request.xml())
        self.assertIsNotNone(request._xml.getroot())
        self.assertEqual(request._xml.getroot().attrib.get('version'), '2.0')

        result = request.execute()
        self.assertTrue(result)


class SubscriptionRequest_Test(unittest.TestCase):
    def test_SubscriptionRequest(self):

        subscriber_ref = 'PY_TEST_SUBSCRIBER'
        
        request = SubscriptionRequest(
            'http://127.0.0.1', 
            8080, 
            subscriber_ref
        )
        
        self.assertIsNotNone(request.xml())
        self.assertEqual(request._xml.getroot().find('.//SubscriptionRequest/RequestorRef').text, subscriber_ref)

        result = request.execute()
        self.assertTrue(result)


class SituationExchangeSubscriptionRequest_Test(unittest.TestCase):
    def test_SituationExchangeSubscriptionRequest(self):

        subscriber_ref = 'PY_TEST_SUBSCRIBER'
        subscription_id = str(uuid.uuid4())
        subscription_termination = timestamp(60 * 60 * 24)
        
        subscription = Subscription(subscription_id, 'http://127.0.0.1', 8080, subscriber_ref, timestamp(60 * 60 * 24))
        request = SituationExchangeSubscriptionRequest(subscription)
        
        self.assertIsNotNone(request.xml())
        self.assertEqual(request._xml.getroot().find('.//SubscriptionRequest/SituationExchangeSubscriptionRequest/SubscriberRef').text, subscriber_ref)
        self.assertEqual(request._xml.getroot().find('.//SubscriptionRequest/SituationExchangeSubscriptionRequest/SubscriptionIdentifier').text, subscription_id)
        self.assertEqual(request._xml.getroot().find('.//SubscriptionRequest/SituationExchangeSubscriptionRequest/InitialTerminationTime').text, subscription_termination)

        result = request.execute()
        self.assertTrue(result)
