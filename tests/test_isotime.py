import unittest
import datetime

from vdv736.isotime import timestamp


class Timestamp_Test(unittest.TestCase):
    def test_timestamp(self):
        additional_seconds = [15, 60, 60 * 60, 60 * 60 * 24]

        for s in additional_seconds:
            reference_timestamp = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
            reference_timestamp = reference_timestamp + datetime.timedelta(seconds=s)

            self.assertEqual(timestamp(s), reference_timestamp.isoformat())
            self.assertTrue(timestamp(s).endswith('+00:00') or timestamp(s).endswith('Z'), timestamp(s))
