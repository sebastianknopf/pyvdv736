import unittest

from vdv736.subscriber import SubscriberController


class SubscriberController_Test(unittest.TestCase):

    def test_SubscriberController(self):

        subscriber = SubscriberController()
        subscription_id = subscriber.subscribe('http://127.0.0.1', 8080, 'PY_TEST_SUBSCRIBER')

        self.assertGreater(len(subscriber._subscriptions), 0)
        self.assertIsNotNone(subscription_id)

        result = subscriber.unsubscribe(subscription_id)

        self.assertEqual(len(subscriber._subscriptions), 0)
        self.assertTrue(result)