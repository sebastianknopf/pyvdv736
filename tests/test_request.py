import unittest
import uuid

from vdv736.isotime import timestamp
from vdv736.model import Subscription
from vdv736.request import SiriRequest
from vdv736.request import SubscriptionRequest
from vdv736.request import SituationExchangeSubscriptionRequest

from vdv736.sirixml import get_value as sirixml_get_value
from vdv736.sirixml import get_attribute as sirixml_get_attribue


class SiriRequest_Test(unittest.TestCase):
    def test_SiriRequest(self):

        request = SiriRequest()

        self.assertIsNotNone(request.xml())
        self.assertEqual(sirixml_get_attribue(request, 'Siri.version'), '2.0')


class SubscriptionRequest_Test(unittest.TestCase):
    def test_SubscriptionRequest(self):

        subscriber_ref = 'PY_TEST_SUBSCRIBER'
        
        request = SubscriptionRequest(
            subscriber_ref
        )
        
        self.assertIsNotNone(request.xml())
        self.assertEqual(sirixml_get_value(request, 'Siri.SubscriptionRequest.RequestorRef'), subscriber_ref)


class SituationExchangeSubscriptionRequest_Test(unittest.TestCase):
    def test_SituationExchangeSubscriptionRequest(self):

        subscriber_ref = 'PY_TEST_SUBSCRIBER'
        subscription_id = str(uuid.uuid4())
        subscription_termination = timestamp(60 * 60 * 24)
        
        subscription = Subscription.create(
            subscription_id, 
            'http://127.0.0.1', 
            8080, 
            'https',
            subscriber_ref, 
            timestamp(60 * 60 * 24)
        )

        request = SituationExchangeSubscriptionRequest(subscription)
        
        self.assertIsNotNone(request.xml())
        self.assertEqual(sirixml_get_value(request, 'Siri.SubscriptionRequest.SituationExchangeSubscriptionRequest.SubscriberRef'), subscriber_ref)
        self.assertEqual(sirixml_get_value(request, 'Siri.SubscriptionRequest.SituationExchangeSubscriptionRequest.SubscriptionIdentifier'), subscription_id)
        self.assertEqual(sirixml_get_value(request, 'Siri.SubscriptionRequest.SituationExchangeSubscriptionRequest.InitialTerminationTime'), subscription_termination)

