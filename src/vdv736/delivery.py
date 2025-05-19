import uuid

from abc import ABC
from lxml.etree import cleanup_namespaces
from lxml.etree import tostring
from lxml.objectify import deannotate
from lxml.objectify import fromstring
from lxml.objectify import Element

from .isotime import timestamp
from .model import Subscription


class SiriDelivery(ABC):

    def __init__(self):
        self.Siri = Element('Siri', xmlns='http://www.siri.org.uk/siri', version='2.1')

    def xml(self) -> str:
        deannotate(self.Siri)
        cleanup_namespaces(self.Siri)

        return tostring(self.Siri, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    

class ServiceDelivery(SiriDelivery):

    def __init__(self, producer_ref: str, more_data=False):
        self.Siri = Element('Siri', xmlns='http://www.siri.org.uk/siri', version='2.1')

        self.Siri.ServiceDelivery = Element('ServiceDelivery')
        self.Siri.ServiceDelivery.ResponseTimestamp = timestamp()
        self.Siri.ServiceDelivery.ProducerRef = producer_ref
        self.Siri.ServiceDelivery.ResponseMessageIdentifier = str(uuid.uuid4())
        self.Siri.ServiceDelivery.Status = True
        self.Siri.ServiceDelivery.MoreData = more_data


class SituationExchangeDelivery(ServiceDelivery):

    def __init__(self, producer_ref: str, subscription: Subscription):
        super().__init__(producer_ref)

        self.Siri.ServiceDelivery.SituationExchangeDelivery = Element('SituationExchangeDelivery', version='2.1')
        self.Siri.ServiceDelivery.SituationExchangeDelivery.ResponseTimestamp = timestamp()

        if subscription is not None:
            self.Siri.ServiceDelivery.SituationExchangeDelivery.SubscriberRef = subscription.subscriber
            self.Siri.ServiceDelivery.SituationExchangeDelivery.SubscriptionRef = subscription.id
            
        self.Siri.ServiceDelivery.SituationExchangeDelivery.Situations = Element('Situations')

    def add_situation(self, situation):
        self.Siri.ServiceDelivery.SituationExchangeDelivery.Situations.append(situation)


def xml2siri_delivery(xml: str) -> SiriDelivery:
    request = SiriDelivery()
    request.Siri = fromstring(xml)

    return request