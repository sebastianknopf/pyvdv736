import logging
import requests

from abc import ABC
from lxml.etree import tostring
from lxml.etree import Element, SubElement, ElementTree

from .isotime import timestamp
from .model import Subscription


class SiriRequest(ABC):

    def __init__(self, host: str, port: int):
        self._address = f"{host}:{port}"

        root = Element('Siri', xmlns='http://www.siri.org.uk/siri', version='2.0')
        self._xml = ElementTree(root)
    
    def execute(self) -> bool:
        try:
            headers = {
                "Content-Type": "text/xml"
            }
            
            response = requests.post(self._address, headers=headers, data=self.xml())
            
            return response.status_code == 200
        except Exception as exception:
            logging.exception(exception)

        return False
    
    def xml(self) -> str:
        return tostring(self._xml, pretty_print=True, xml_declaration=True, encoding='UTF-8')


class SubscriptionRequest(SiriRequest):

    def __init__(self, subscription_host: str, subscription_port: int, subscriber_ref: str):
        super().__init__(subscription_host, subscription_port)

        SubElement(self._xml.getroot(), 'SubscriptionRequest')
        SubElement(self._xml.getroot().find('.//SubscriptionRequest'), 'RequestTimestamp').text = timestamp()
        SubElement(self._xml.getroot().find('.//SubscriptionRequest'), 'RequestorRef').text = subscriber_ref
        SubElement(self._xml.getroot().find('.//SubscriptionRequest'), 'SubscriptionContext')
        SubElement(self._xml.getroot().find('.//SubscriptionRequest/SubscriptionContext'), 'HeartbeatInterval').text = 'PT5M'


class SituationExchangeSubscriptionRequest(SubscriptionRequest):

    def __init__(self, subscription: Subscription):
        super().__init__(subscription.host, subscription.port, subscription.subscriber)

        SubElement(self._xml.getroot().find('.//SubscriptionRequest'), 'SituationExchangeSubscriptionRequest')
        SubElement(self._xml.getroot().find('.//SubscriptionRequest/SituationExchangeSubscriptionRequest'), 'SubscriberRef').text = subscription.subscriber
        SubElement(self._xml.getroot().find('.//SubscriptionRequest/SituationExchangeSubscriptionRequest'), 'SubscriptionIdentifier').text = subscription.id
        SubElement(self._xml.getroot().find('.//SubscriptionRequest/SituationExchangeSubscriptionRequest'), 'InitialTerminationTime').text = subscription.termination
        SubElement(self._xml.getroot().find('.//SubscriptionRequest/SituationExchangeSubscriptionRequest'), 'SituationExchangeRequest', version='2.0')
        SubElement(self._xml.getroot().find('.//SubscriptionRequest/SituationExchangeSubscriptionRequest/SituationExchangeRequest'), 'RequestTimestamp').text = timestamp()

        