# PyVDV736
Simple reference implementation for [VDV736](https://www.vdv.de/736-2-sds.pdfx?forced=true) subscriber and publisher written in Python. [VDV736](https://www.vdv.de/736-2-sds.pdfx?forced=true) is a data standard based on [SIRI-SX](https://github.com/SIRI-CEN/SIRI) for public transport situation exchange.

## Situation Exchange in VDV736
Exchanging public transport situations works with a realtime capable setup using a publish/subscribe mechanism. To get this working, the publisher (in most cases called 'server') as well as the subscriber (in most cases called 'client') needs to be callable via an HTTP(S) interface.

A subscription then works as follows:
- The subscriber registers at the publisher with its participant ID (aka 'Leitstellenkennung') and some basic subscription parameters
- The publisher stores this subscription and every time a new public transport situation is published, the publisher calls the subscriber's endpoint with a body containing data
- At the end, the subscribers terminates his subscription sending a request to the publisher again, stating that the existing subscription should be deleted

This way, data are only transferred, when they're updated in realtime without polling. Other well-known public transport protocols (like VDV453, VDV454, SIRI) work exactly the same. A digital data hub (aka 'Datendrehscheibe') combines the role of the publisher and subscriber.

_Note: SIRI-SX offers also the option for fetching public transport situations using a simple GET request. VDV736 states that only publish/subscribe is supported. Hence, the request endpoint of the publisher is only experimental and not supported officially._

## Configuration
There's a YAML file which contains basic configuration for all participants (subscriber as well as publisher). See following example for reference:

```yaml
PY_TEST_PUBLISHER:
  host: "127.0.0.1"
  port: 9091
  protocol: http
  single_endpoint: null
  status_endpoint: /status
  subscribe_endpoint: /subscribe
  unsubscribe_endpoint: /unsubscribe
  request_endpoint: /request
  delivery_endpoint: null
```

The top level keys are the participant IDs, which must be agreed between the participants at first. Each participant system needs to have an IP address or hostname, a port and a protocol which should be used for access. You can also specify the endpoints for the different actions a participant is providing.

_Note: There're some implementations which do not use special endpoints for each request type. To deal with them, set the property `single_endpoint` to a value other than `null`. This leads to the other endpoint configurations to become ignored and works for remote publishers as well as for the subscriber and publisher in this implementation._

## Installation & Usage
Using this library is quite simple. Install it using

`pip install pyvdv736`

Then use a `Subscriber` or `Publisher` object to work with. See following example:

```python
from vdv736.subscriber import Subscriber
from vdv736.delivery import SiriDelivery

def on_delivery(delivery: SiriDelivery) -> None:
    print('Delivery callback called...')

with Subscriber('PY_TEST_SUBSCRIBER', './participants.yaml') as subscriber:
    subscriber.set_callbacks(on_delivery)
    
    subscription_id = subscriber.subscribe('PY_TEST_PUBLISHER')
    ...
    subscriber.unsubscribe(subscription_id)

    while True:
        pass
```

See sample scripts in the [demo](/demo) folder.

## License
This project is licensed under the Apache License. See [LICENSE.md](LICENSE.md) for more information.