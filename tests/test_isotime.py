import unittest
import datetime

from vdv736.isotime import timestamp
from vdv736.isotime import interval


class Timestamp_Test(unittest.TestCase):
    def test_timestamp(self):
        seconds = [15, 60, 60 * 60, 60 * 60 * 24]

        for s in seconds:
            reference_timestamp = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
            reference_timestamp = reference_timestamp + datetime.timedelta(seconds=s)

            self.assertEqual(timestamp(s), reference_timestamp.isoformat())
            self.assertTrue(timestamp(s).endswith('+00:00') or timestamp(s).endswith('Z'), timestamp(s))

    def test_interval(self):
        self.assertEqual(interval(0, 0, 0, 1, 0, 0), 'PT1H')
        self.assertEqual(interval(1, 0, 5, 0, 10, 0), 'P1Y5DT10M')
        self.assertEqual(interval(0, 0, 0, 0, 0, 15), 'PT15S')
        self.assertEqual(interval(0, 0, 0, 0, 5, 0), 'PT5M')
