import os
import responses
import unittest
import unittest.mock

from vdv736.delivery import xml2siri_delivery
from vdv736.delivery import SiriDelivery
from vdv736.handler import SituationProgressHandler
from vdv736.isotime import timestamp
from vdv736.sirixml import get_elements as sirixml_get_elements

class SubscriberDirectRequest_Test(unittest.TestCase):

    def _extract_first_situation(self, filename: str) -> object:
        xml_filename = os.path.join(os.path.dirname(__file__), filename)
        with open(xml_filename, 'rb') as xml_file:
            xml_content = xml_file.read()

        siri_delivery = xml2siri_delivery(xml_content)

        return sirixml_get_elements(siri_delivery, 'Siri.ServiceDelivery.SituationExchangeDelivery.Situations.PtSituationElement')[0]

    def test_DecideWhetherToDelete_WithClosingSituation(self):

        pts = self._extract_first_situation('data/xml/SampleServiceDeliveryWithClosingSituation.xml')

        handler = SituationProgressHandler()

        result = handler.handle_situation(pts)
        self.assertEqual(False, result)

    def test_DecideWhetherToDelete_WithRecentlyUpdatedClosingSituation(self):

        pts = self._extract_first_situation('data/xml/SampleServiceDeliveryWithClosingSituation.xml')
        pts.VersionedAtTime = timestamp(-120)

        handler = SituationProgressHandler()

        result = handler.handle_situation(pts)
        self.assertEqual(True, result)
        

        

    	