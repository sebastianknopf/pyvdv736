import yaml

class ParticipantConfig:

    def __init__(self, participant_config_filename):

        self.participants = dict()

        with open(participant_config_filename) as participant_config_file:
                default_config = {
                    'host': '127.0.0.1',
                    'port': 9090,
                    'protocol': 'http',
                    'status_endpoint': '/status',
                    'subscribe_endpoint': '/subscribe',
                    'unsubscribe_endpoint': '/unsubscribe',
                    'request_endpoint': '/request',
                    'delivery_endpoint': '/delivery'
                }

                configs = yaml.safe_load(participant_config_file)
                for participant_id, participant_config in configs.items():
                    self.participants[participant_id] = self._merge_config(
                        default_config, 
                        participant_config
                    )

    def _merge_config(self, defaults, actual):
        if isinstance(defaults, dict) and isinstance(actual, dict):
            return {k: self._merge_config(defaults.get(k, {}), actual.get(k, {})) for k in set(defaults) | set(actual)}
        
        return actual if actual else defaults