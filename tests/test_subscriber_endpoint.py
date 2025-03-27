import os
import unittest
import unittest.mock

from fastapi.testclient import TestClient

from vdv736.model import Subscription
from vdv736.subscriber import SubscriberEndpoint
from vdv736.response import xml2siri_response

class SubscriberEndpoint_Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.endpoint = SubscriberEndpoint('TEST')

        # setup a virtual subscription, otherwise the subscriber will fail
        # see #21 for details
        virtual_subscription = Subscription()
        virtual_subscription.remote_service_participant_ref = 'TEST-PUBLISHER'

        cls.endpoint._local_node_database.add_subscription('1', virtual_subscription)

        # create test client
        cls.client = TestClient(cls.endpoint.create_endpoint(
            '/vdv736'
        ))

        return super().setUpClass()
    
    def test_SampleServiceDelivery(self):
        xml_filename = os.path.join(os.path.dirname(__file__), 'data/xml/SampleServiceDelivery.xml')
        with open(xml_filename, 'r') as xml_file:
            response = self.client.post('/vdv736', content=xml_file.read())

            self.assertEqual(200, response.status_code)

            siri_response = xml2siri_response(response.content)
            self.assertEqual(True, siri_response.Siri.DataReceivedAcknowledgement.Status)

    def test_SampleServiceDeliveryWithCallbacks(self):
        on_delivery_callback = unittest.mock.Mock()
            
        self.endpoint.set_callbacks(on_delivery_callback)
        
        xml_filename = os.path.join(os.path.dirname(__file__), 'data/xml/SampleServiceDelivery.xml')
        with open(xml_filename, 'r') as xml_file:
            
            response = self.client.post('/vdv736', content=xml_file.read())

            self.assertEqual(200, response.status_code)
            on_delivery_callback.assert_called()

            siri_response = xml2siri_response(response.content)
            self.assertEqual(True, siri_response.Siri.DataReceivedAcknowledgement.Status)

        self.endpoint.set_callbacks(None)

    def test_SampleServiceDeliveryWithInvalidPublisher(self):
        xml_filename = os.path.join(os.path.dirname(__file__), 'data/xml/SampleServiceDeliveryWithInvalidPublisher.xml')
        with open(xml_filename, 'r') as xml_file:
            response = self.client.post('/vdv736', content=xml_file.read())

            self.assertEqual(401, response.status_code)
    
    def test_InvalidXmlData(self):
        xml_filename = os.path.join(os.path.dirname(__file__), 'data/xml/InvalidXmlData.xml')
        with open(xml_filename, 'r') as xml_file:
            response = self.client.post('/vdv736', content=xml_file.read())

            self.assertEqual(400, response.status_code)

    def test_InvalidEndpoint(self):
        response = self.client.post('/someInvalidEndpoint')
        self.assertEqual(404, response.status_code)

    def test_InvalidMethod(self):
        response = self.client.get('/vdv736')
        self.assertEqual(405, response.status_code)

    @classmethod
    def tearDownClass(cls):

        # close local node database in order to cleanup endpoint data
        # note: normally, this would be done by the Subscriber class, as the endpoint
        # is started as thread of the subscriber!
        cls.endpoint._local_node_database.close(True)

        return super().tearDownClass()
            