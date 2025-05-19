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
    

class CheckStatusResponse(SiriResponse):

     def __init__(self, service_started_time: str):
         super().__init__()

         self.Siri.CheckStatusResponse = Element('CheckStatusResponse')
         self.Siri.CheckStatusResponse.ResponseTimestamp = timestamp()
         self.Siri.CheckStatusResponse.Status = True
         self.Siri.CheckStatusResponse.ValidUntil = ''
         self.Siri.CheckStatusResponse.ShortestPossibleCycle = interval(0, 0, 0, 0, 1, 0)
         self.Siri.CheckStatusResponse.ServiceStartedTime = service_started_time


class SubscriptionResponse(SiriResponse):

    def __init__(self, responder_ref: str, service_started_time: str = None):
        super().__init__()

        self.Siri.SubscriptionResponse = Element('SubscriptionResponse')
        self.Siri.SubscriptionResponse.ResponseTimestamp = Element('ResponseTimestamp')
        self.Siri.SubscriptionResponse.ResponderRef = Element('ResponderRef')
        self.Siri.SubscriptionResponse.ResponseStatus = Element('ResponseStatus')

        self.Siri.SubscriptionResponse.ResponseTimestamp = timestamp()
        self.Siri.SubscriptionResponse.ResponderRef = responder_ref

        if service_started_time is not None:
            self.Siri.SubscriptionResponse.ResponseStatus.ServiceStartedTime = service_started_time        

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


class TerminateSubscriptionResponse(SiriResponse):

    def __init__(self, responder_ref: str):
        super().__init__()

        self.Siri.TerminationSubscriptionResponse = Element('TerminationSubscriptionResponse')
        self.Siri.TerminationSubscriptionResponse.ResponseTimestamp = timestamp()
        self.Siri.TerminationSubscriptionResponse.ResponderRef = responder_ref

    def ok(self, subscriber_ref: str, subscription_id: str):
        self.add_ok(subscriber_ref, subscription_id)

    def error(self, subscription_id: str):
        self.add_error(subscription_id)

    def add_ok(self, subscriber_ref: str, subscription_id: str):
        
        termination_response_status = Element('TerminationResponseStatus')
        termination_response_status.ResponseTimestamp = timestamp()
        termination_response_status.SubscriberRef = subscriber_ref
        termination_response_status.SubscriptionRef = subscription_id
        termination_response_status.Status = True

        self.Siri.TerminationSubscriptionResponse.append(termination_response_status)

    def add_error(self, subscription_id: str):

        termination_response_status = Element('TerminationResponseStatus')
        termination_response_status.SubscriptionRef = subscription_id
        termination_response_status.Status = False

        termination_response_status.ErrorCondition = Element('ErrorCondition')
        termination_response_status.ErrorCondition.OtherError = Element('OtherError')

        self.Siri.TerminationSubscriptionResponse.append(termination_response_status)


class DataReceivedAcknowledgement(SiriResponse):

    def __init__(self, consumer_ref, request_message_ref: str):
        super().__init__()

        self.Siri.DataReceivedAcknowledgement = Element('DataReceivedAcknowledgement')
        self.Siri.DataReceivedAcknowledgement.ResponseTimestamp = timestamp()
        self.Siri.DataReceivedAcknowledgement.ConsumerRef = consumer_ref
        self.Siri.DataReceivedAcknowledgement.RequestMessageRef = request_message_ref

    def ok(self):
        self.Siri.DataReceivedAcknowledgement.Status = True

    def error(self):
        self.Siri.DataReceivedAcknowledgement.Status = False

def xml2siri_response(xml: str) -> SiriResponse:
    response = SiriResponse()
    response.Siri = fromstring(xml)

    return response