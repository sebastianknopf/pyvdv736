from abc import ABC
from lxml.etree import cleanup_namespaces
from lxml.etree import tostring
from lxml.objectify import deannotate
from lxml.objectify import fromstring
from lxml.objectify import Element

from .isotime import timestamp
from .isotime import interval
from .model import Subscription


class SiriRequest(ABC):

    def __init__(self):
        self.Siri = Element('Siri', xmlns='http://www.siri.org.uk/siri', version='2.0')
    
    def xml(self) -> str:
        deannotate(self.Siri)
        cleanup_namespaces(self.Siri)

        return tostring(self.Siri, pretty_print=True, xml_declaration=True, encoding='UTF-8')


class SubscriptionRequest(SiriRequest):

    def __init__(self, subscriber_ref: str):
        super().__init__()

        self.Siri.SubscriptionRequest = Element('SubscriptionRequest')
        self.Siri.SubscriptionRequest.RequestTimestamp = timestamp()
        self.Siri.SubscriptionRequest.RequestorRef = subscriber_ref

        self.Siri.SubscriptionRequest.SubscriptionContext = Element('SubscriptionContext')
        self.Siri.SubscriptionRequest.SubscriptionContext.HeartbeatInterval = interval(0, 0, 0, 0, 5, 0)


class SituationExchangeSubscriptionRequest(SubscriptionRequest):

    def __init__(self, subscription: Subscription):
        super().__init__(subscription.subscriber)

        self.Siri.SubscriptionRequest.SituationExchangeSubscriptionRequest = Element('SituationExchangeSubscriptionRequest')
        self.Siri.SubscriptionRequest.SituationExchangeSubscriptionRequest.SubscriberRef = subscription.subscriber
        self.Siri.SubscriptionRequest.SituationExchangeSubscriptionRequest.SubscriptionIdentifier = subscription.id
        self.Siri.SubscriptionRequest.SituationExchangeSubscriptionRequest.InitialTerminationTime = subscription.termination

        self.Siri.SubscriptionRequest.SituationExchangeSubscriptionRequest.SituationExchangeRequest = Element('SituationExchangeRequest')
        self.Siri.SubscriptionRequest.SituationExchangeSubscriptionRequest.SituationExchangeRequest.RequestTimestamp = timestamp()


def xml2siri_request(xml: str) -> SiriRequest:
    request = SiriRequest()
    request.Siri = fromstring(xml)

    return request

        