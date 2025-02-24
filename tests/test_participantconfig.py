import os
import unittest

from vdv736.participantconfig import ParticipantConfig

class SiriRequest_Test(unittest.TestCase):

    def test_withFullConfig(self):

        participant_config = ParticipantConfig(
            os.path.join(os.path.dirname(__file__), 'data/yaml/participants_with_full_config.yaml')
        )

        self.assertEqual(2, len(participant_config.participants))
        self.assertEqual('127.0.0.1', participant_config.participants['PY_TEST_PUBLISHER']['host'])
        self.assertEqual(9091, participant_config.participants['PY_TEST_PUBLISHER']['port'])
        self.assertEqual('http', participant_config.participants['PY_TEST_PUBLISHER']['protocol'])
        self.assertEqual(None, participant_config.participants['PY_TEST_PUBLISHER']['single_endpoint'])
        self.assertEqual('/status', participant_config.participants['PY_TEST_PUBLISHER']['status_endpoint'])
        self.assertEqual('/subscribe', participant_config.participants['PY_TEST_PUBLISHER']['subscribe_endpoint'])
        self.assertEqual('/unsubscribe', participant_config.participants['PY_TEST_PUBLISHER']['unsubscribe_endpoint'])
        self.assertEqual('/request', participant_config.participants['PY_TEST_PUBLISHER']['request_endpoint'])
        self.assertEqual(None, participant_config.participants['PY_TEST_PUBLISHER']['delivery_endpoint'])

    def test_withPartialConfig(self):

        participant_config = ParticipantConfig(
            os.path.join(os.path.dirname(__file__), 'data/yaml/participants_with_partial_config.yaml')
        )

        self.assertEqual(2, len(participant_config.participants))
        self.assertEqual('127.0.0.1', participant_config.participants['PY_TEST_SUBSCRIBER']['host'])
        self.assertEqual(9090, participant_config.participants['PY_TEST_SUBSCRIBER']['port'])
        self.assertEqual('http', participant_config.participants['PY_TEST_SUBSCRIBER']['protocol'])
        self.assertEqual('/server', participant_config.participants['PY_TEST_SUBSCRIBER']['single_endpoint'])
        self.assertEqual('/status', participant_config.participants['PY_TEST_SUBSCRIBER']['status_endpoint'])
        self.assertEqual('/subscribe', participant_config.participants['PY_TEST_SUBSCRIBER']['subscribe_endpoint'])
        self.assertEqual('/unsubscribe', participant_config.participants['PY_TEST_SUBSCRIBER']['unsubscribe_endpoint'])
        self.assertEqual('/request', participant_config.participants['PY_TEST_SUBSCRIBER']['request_endpoint'])
        self.assertEqual('/delivery', participant_config.participants['PY_TEST_SUBSCRIBER']['delivery_endpoint'])

    def test_withInvalidConfig(self):
        self.assertRaises(ValueError, ParticipantConfig, os.path.join(os.path.dirname(__file__), 'data/yaml/participants_with_invalid_config.yaml'))