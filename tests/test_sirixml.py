import unittest

from lxml.objectify import fromstring

from vdv736.sirixml import get_attribute as sirixml_get_attribue

class Sirixml_Test(unittest.TestCase):

    def test_get_attribute_withoutNamespaces(self):

        xml = """
        <Siri xmlns="http://www.siri.org.uk/siri" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="2.0">
        </Siri>
        """

        obj = lambda: None
        obj.Siri = fromstring(xml)

        self.assertEqual('2.0', sirixml_get_attribue(obj, 'Siri.version'))
        self.assertEqual(None, sirixml_get_attribue(obj, 'Siri.invalid_attribute'))

    def test_get_attribute_withNamespace(self):

        xml = """
        <Siri xmlns="http://www.siri.org.uk/siri" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="2.0">
        <Situation>
        <Summary xml:lang="DE">This is a sample element</Summary>
        </Situation>
        </Siri>
        """

        obj = lambda: None
        obj.Siri = fromstring(xml)

        self.assertEqual('DE', sirixml_get_attribue(obj, 'Siri.Situation.Summary.{http://www.w3.org/XML/1998/namespace}lang'))
        self.assertEqual(None, sirixml_get_attribue(obj, 'Siri.Situation.Summary.lang'))

