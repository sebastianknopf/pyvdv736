from abc import ABC
from lxml.etree import cleanup_namespaces
from lxml.etree import tostring
from lxml.objectify import deannotate
from lxml.objectify import fromstring
from lxml.objectify import Element

from .isotime import timestamp
from .isotime import interval


class SiriResponse(ABC):

    def __init__(self):
        self.Siri = Element('Siri', xmlns='http://www.siri.org.uk/siri', version='2.0')

    def xml(self) -> str:
        deannotate(self.Siri)
        cleanup_namespaces(self.Siri)

        return tostring(self.Siri, pretty_print=True, xml_declaration=True, encoding='UTF-8') 
    

class SubscriptionResponse(SiriResponse):

    def __init__(self, responder_ref: str):
        super().__init__()

        self.Siri.SubscriptionResponse = Element('SubscriptionResponse')
        self.Siri.SubscriptionResponse.ResponseTimestamp = Element('ResponseTimestamp')
        self.Siri.SubscriptionResponse.ResponderRef = Element('ResponderRef')
        self.Siri.SubscriptionResponse.ResponseStatus = Element('ResponseStatus')

        self.Siri.SubscriptionResponse.ResponseTimestamp = timestamp()
        self.Siri.SubscriptionResponse.ResponderRef = responder_ref        

    def ok(self, subscription_id: str, subscription_termination: str):

        self.Siri.SubscriptionResponse.ResponseStatus.ResponseTimestamp = timestamp()
        self.Siri.SubscriptionResponse.ResponseStatus.SubscriptionRef = subscription_id
        self.Siri.SubscriptionResponse.ResponseStatus.Status = True
        self.Siri.SubscriptionResponse.ResponseStatus.ValidUntil = subscription_termination
        self.Siri.SubscriptionResponse.ResponseStatus.ShortestPossibleCycle = interval(0, 0, 0, 0, 1, 0)

    def error(self, subscription_id: str):
        self.Siri.SubscriptionResponse.ResponseStatus.ResponseTimestamp = timestamp()
        self.Siri.SubscriptionResponse.ResponseStatus.SubscriptionRef = subscription_id
        self.Siri.SubscriptionResponse.ResponseStatus.Status = False

        self.Siri.SubscriptionResponse.ResponseStatus.ErrorCondition = Element('ErrorCondition')


def xml2siri_response(xml: str) -> SiriResponse:
    response = SiriResponse()
    response.Siri = fromstring(xml)

    return response