import os
import responses
import unittest
import unittest.mock

from vdv736.subscriber import Subscriber
from vdv736.request import InvalidMethodError

class SubscriberDirectRequest_Test(unittest.TestCase):

    def setUp(self):
        xml_filename = os.path.join(os.path.dirname(__file__), 'data/xml/SampleServiceDelivery.xml')
        with open(xml_filename, 'r') as xml_file:
            xml_content = xml_file.read()
        
        self.responder = responses.RequestsMock(assert_all_requests_are_fired=False)
        self.responder.start()

        self.responder.add(
            responses.POST,
            'http://127.0.0.1:9091/request',
            body=xml_content,
            content_type='application/xml',
            status=200
        )

        self.responder.add(
            responses.GET,
            'http://127.0.0.1:9091/request',
            body=xml_content,
            content_type='application/xml',
            status=200
        )

    def test_DirectRequestResponse(self):

        configfile = os.path.join(os.path.dirname(__file__), 'data/yaml/participants_testconfig.yaml')        
        with Subscriber('PY_TEST_SUBSCRIBER', configfile, publish_subscribe=False) as subscriber:
            self.assertEqual(True, subscriber.request('PY_TEST_PUBLISHER'))
            self.assertEqual(1, len(subscriber.get_situations()))

    def test_DirectRequestResponseWithCallback(self):
  
        on_delivery_callback = unittest.mock.Mock()
        
        configfile = os.path.join(os.path.dirname(__file__), 'data/yaml/participants_testconfig.yaml')
        with Subscriber('PY_TEST_SUBSCRIBER', configfile, publish_subscribe=False) as subscriber:
            subscriber.set_callbacks(on_delivery_callback)

            self.assertEqual(True, subscriber.request('PY_TEST_PUBLISHER'))
            on_delivery_callback.assert_called()

    def test_DirectRequestResponseUsingGET(self):

        configfile = os.path.join(os.path.dirname(__file__), 'data/yaml/participants_testconfig.yaml')        
        with Subscriber('PY_TEST_SUBSCRIBER', configfile, publish_subscribe=False) as subscriber:
            self.assertEqual(True, subscriber.request('PY_TEST_PUBLISHER', method='GET'))
            self.assertEqual(1, len(subscriber.get_situations()))

    def test_DirectRequestResponseUsingInvalidMethod(self):

        configfile = os.path.join(os.path.dirname(__file__), 'data/yaml/participants_testconfig.yaml')        
        with Subscriber('PY_TEST_SUBSCRIBER', configfile, publish_subscribe=False) as subscriber:
            with self.assertRaises(InvalidMethodError):
                subscriber.request('PY_TEST_PUBLISHER', method='TESTMETHOD')
            
    def tearDown(self):
        self.responder.stop()
        self.responder.reset()

        return super().tearDownClass()