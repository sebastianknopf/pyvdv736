import http.server
import logging
import os
import socketserver
import threading
import unittest
import unittest.mock

from vdv736.subscriber import Subscriber


class MockHttpPublisherHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/request':
            self.send_response(200)
            self.send_header("Content-type", "application/xml")
            self.end_headers()

            xml_filename = os.path.join(os.path.dirname(__file__), 'data/xml/SampleServiceDelivery.xml')
            with open(xml_filename, 'rb') as xml_file:
                xml_content = xml_file.read()

            self.wfile.write(xml_content)
        else:
            self.send_response(200)

    def log_message(self, format, *args):
        pass


class SubscriberDirectRequest_Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.server = socketserver.TCPServer(("localhost", 9091), MockHttpPublisherHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.daemon = True
        cls.thread.start()

        logging.disable(logging.CRITICAL)

        configfile = os.path.join(os.path.dirname(__file__), 'data/yaml/participants_testconfig.yaml')
        cls.subscriber = Subscriber('PY_TEST_SUBSCRIBER', configfile)
        cls.subscriber.__enter__()

    def test_DirectRequestResponse(self):
        self.assertEqual(True, self.subscriber.request('PY_TEST_PUBLISHER'))
        self.assertEqual(1, len(self.subscriber.get_situations()))

    def test_DirectRequestResponseWithCallback(self):
        on_delivery_callback = unittest.mock.Mock()
        
        self.subscriber.set_callbacks(on_delivery_callback)

        self.assertEqual(True, self.subscriber.request('PY_TEST_PUBLISHER'))
        on_delivery_callback.assert_called()
            

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

        logging.disable(logging.NOTSET)

        cls.subscriber.__exit__(None, None, None)

        return super().tearDownClass()