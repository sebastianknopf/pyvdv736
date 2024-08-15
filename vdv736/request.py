import logging
import requests

from abc import ABC
from lxml.etree import tostring
from lxml.etree import Element, SubElement, ElementTree

from .isotime import timestamp
from .isotime import interval
from .model import Subscription


class SiriRequest(ABC):

    def __init__(self, host: str, port: int, subscribe_endpoint: str):
        self._address = f"{host}:{port}{subscribe_endpoint}"

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

    def __init__(self, subscription_host: str, subscription_port: int, subscriber_ref: str, subscribe_endpoint: str):
        super().__init__(subscription_host, subscription_port, subscribe_endpoint)

        SubElement(self._xml.getroot(), 'SubscriptionRequest')
        SubElement(self._xml.find('.//SubscriptionRequest'), 'RequestTimestamp').text = timestamp()
        SubElement(self._xml.find('.//SubscriptionRequest'), 'RequestorRef').text = subscriber_ref
        SubElement(self._xml.find('.//SubscriptionRequest'), 'SubscriptionContext')
        SubElement(self._xml.find('.//SubscriptionRequest/SubscriptionContext'), 'HeartbeatInterval').text = interval(0, 0, 0, 0, 5, 0)


class SituationExchangeSubscriptionRequest(SubscriptionRequest):

    def __init__(self, subscription: Subscription):
        super().__init__(subscription.host, subscription.port, subscription.subscriber, subscription.subscribe_endpoint)

        SubElement(self._xml.find('.//SubscriptionRequest'), 'SituationExchangeSubscriptionRequest')
        SubElement(self._xml.find('.//SubscriptionRequest/SituationExchangeSubscriptionRequest'), 'SubscriberRef').text = subscription.subscriber
        SubElement(self._xml.find('.//SubscriptionRequest/SituationExchangeSubscriptionRequest'), 'SubscriptionIdentifier').text = subscription.id
        SubElement(self._xml.find('.//SubscriptionRequest/SituationExchangeSubscriptionRequest'), 'InitialTerminationTime').text = subscription.termination
        SubElement(self._xml.find('.//SubscriptionRequest/SituationExchangeSubscriptionRequest'), 'SituationExchangeRequest', version='2.0')
        SubElement(self._xml.find('.//SubscriptionRequest/SituationExchangeSubscriptionRequest/SituationExchangeRequest'), 'RequestTimestamp').text = timestamp()

        