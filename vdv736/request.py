from abc import ABC
from lxml.etree import cleanup_namespaces
from lxml.etree import tostring
from lxml.objectify import deannotate
from lxml.objectify import fromstring
from lxml.objectify import Element

from .isotime import timestamp
from .isotime import interval
from .model import Subscription


class InvalidMethodError(Exception):
    pass

class SiriRequest(ABC):

    def __init__(self):
        self.Siri = Element('Siri', xmlns='http://www.siri.org.uk/siri', version='2.0')
    
    def xml(self) -> str:
        deannotate(self.Siri)
        cleanup_namespaces(self.Siri)

        return tostring(self.Siri, pretty_print=True, xml_declaration=True, encoding='UTF-8')


class CheckStatusRequest(SiriRequest):

    def __init__(self, subscription: Subscription):
        super().__init__()

        self.Siri.CheckStatusRequest = Element('CheckStatusRequest', version='2.0')
        self.Siri.CheckStatusRequest.RequestTimestamp = timestamp()
        self.Siri.CheckStatusRequest.RequestorRef = subscription.subscriber


class SubscriptionRequest(SiriRequest):

    def __init__(self, subscriber_ref: str):
        super().__init__()

        self.Siri.SubscriptionRequest = Element('SubscriptionRequest')
        self.Siri.SubscriptionRequest.RequestTimestamp = timestamp()
        self.Siri.SubscriptionRequest.RequestorRef = subscriber_ref


class ServiceRequest(SiriRequest):

    def __init__(self, subscriber_ref: str):
        super().__init__()

        self.Siri.ServiceRequest = Element('ServiceRequest')
        self.Siri.ServiceRequest.RequestTimestamp = timestamp()
        self.Siri.ServiceRequest.RequestorRef = subscriber_ref


class TerminateSubscriptionRequest(SiriRequest):

    def __init__(self, subscriber_ref: str):
        super().__init__()

        self.Siri.TerminateSubscriptionRequest = Element('TerminateSubscriptionRequest')
        self.Siri.TerminateSubscriptionRequest.RequestTimestamp = timestamp()
        self.Siri.TerminateSubscriptionRequest.RequestorRef = subscriber_ref

    def subscription(self, subscriber_ref: str, subscription_id: str) -> None:
        self.Siri.TerminateSubscriptionRequest.SubscriberRef = subscriber_ref
        self.Siri.TerminateSubscriptionRequest.SubscriptionRef = subscription_id

    def all(self):
        self.Siri.TerminateSubscriptionRequest.All = Element('All')


class SituationExchangeSubscriptionRequest(SubscriptionRequest):

    def __init__(self, subscription: Subscription):
        super().__init__(subscription.subscriber)

        self.Siri.SubscriptionRequest.SituationExchangeSubscriptionRequest = Element('SituationExchangeSubscriptionRequest')
        self.Siri.SubscriptionRequest.SituationExchangeSubscriptionRequest.SubscriberRef = subscription.subscriber
        self.Siri.SubscriptionRequest.SituationExchangeSubscriptionRequest.SubscriptionIdentifier = subscription.id
        self.Siri.SubscriptionRequest.SituationExchangeSubscriptionRequest.InitialTerminationTime = subscription.termination

        self.Siri.SubscriptionRequest.SituationExchangeSubscriptionRequest.SituationExchangeRequest = Element('SituationExchangeRequest')
        self.Siri.SubscriptionRequest.SituationExchangeSubscriptionRequest.SituationExchangeRequest.RequestTimestamp = timestamp()


class SituationExchangeRequest(ServiceRequest):

    def __init__(self, subscriber_ref: str):
        super().__init__(subscriber_ref)

        self.Siri.ServiceRequest.SituationExchangeRequest = Element('SituationExchangeRequest', version='2.0')
        self.Siri.ServiceRequest.SituationExchangeRequest.RequestTimestamp = timestamp()


def xml2siri_request(xml: str) -> SiriRequest:
    request = SiriRequest()
    request.Siri = fromstring(xml)

    return request

        