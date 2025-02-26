import os
import unittest
import unittest.mock

from fastapi.testclient import TestClient

from vdv736.publisher import PublisherEndpoint
from vdv736.response import xml2siri_response
from vdv736.sirixml import get_elements as sirixml_get_elements

class SubscriberEndpoint_Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.endpoint = PublisherEndpoint('TEST')

        cls.client = TestClient(cls.endpoint.create_endpoint(
            'TEST', 
            '/vdv736'
        ))

        return super().setUpClass()
    
    def test_SampleSubscriptionRequest(self):
        on_subscribe_callback = unittest.mock.Mock()
        on_unsubscribe_callback = unittest.mock.Mock()

        self.endpoint.set_callbacks(on_subscribe_callback=on_subscribe_callback, on_unsubscribe_callback=on_unsubscribe_callback)
        
        xml_filename = os.path.join(os.path.dirname(__file__), 'data/xml/SampleSubscriptionRequest.xml')
        with open(xml_filename, 'r') as xml_file:
            response = self.client.post('/vdv736', content=xml_file.read())

            self.assertEqual(200, response.status_code)
            on_subscribe_callback.assert_called()
            on_unsubscribe_callback.assert_not_called()

            siri_response = xml2siri_response(response.content)
            self.assertEqual(True, siri_response.Siri.SubscriptionResponse.ResponseStatus.Status)

    def test_SampleTerminateSpecificSubscriptionRequest(self):
        on_subscribe_callback = unittest.mock.Mock()
        on_unsubscribe_callback = unittest.mock.Mock()

        self.endpoint.set_callbacks(on_subscribe_callback=on_subscribe_callback, on_unsubscribe_callback=on_unsubscribe_callback)
        
        xml_filename = os.path.join(os.path.dirname(__file__), 'data/xml/SampleTerminateSpecificSubscriptionRequest.xml')
        with open(xml_filename, 'r') as xml_file:
            response = self.client.post('/vdv736', content=xml_file.read())

            self.assertEqual(200, response.status_code)
            on_subscribe_callback.assert_not_called()
            on_unsubscribe_callback.assert_called()

            siri_response = xml2siri_response(response.content)
            termination_response_status = sirixml_get_elements(siri_response, 'Siri.TerminationSubscriptionResponse.TerminationResponseStatus')
            for trs in termination_response_status:
                self.assertEqual(True, trs.Status)

    def test_SampleTerminateSubscriptionRequest(self):
        on_subscribe_callback = unittest.mock.Mock()
        on_unsubscribe_callback = unittest.mock.Mock()

        self.endpoint.set_callbacks(on_subscribe_callback=on_subscribe_callback, on_unsubscribe_callback=on_unsubscribe_callback)
        
        xml_filename = os.path.join(os.path.dirname(__file__), 'data/xml/SampleTerminateSubscriptionRequest.xml')
        with open(xml_filename, 'r') as xml_file:
            response = self.client.post('/vdv736', content=xml_file.read())

            self.assertEqual(200, response.status_code)
            on_subscribe_callback.assert_not_called()
            # on_unsubscribe_callback.assert_called() # cannot be called here, since test_SampleTerminateSpecificSubscriptionRequest already terminated every subscription on the test publisher

            siri_response = xml2siri_response(response.content)
            termination_response_status = sirixml_get_elements(siri_response, 'Siri.TerminationSubscriptionResponse.TerminationResponseStatus')
            
            self.assertEqual(0, len(termination_response_status))        

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
            