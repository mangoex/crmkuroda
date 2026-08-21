"""Unit tests for Scheduler Timezone Configuration and Business Dates."""

import unittest
from datetime import date
from zoneinfo import ZoneInfo
from unittest.mock import patch, MagicMock, PropertyMock

from app.core.config import settings
from app.core.scheduler import _business_today, start_scheduler, scheduler


class TestSchedulerTimezone(unittest.TestCase):
    def test_business_today_returns_valid_date(self):
        today = _business_today()
        self.assertIsInstance(today, date)

    def test_start_scheduler_configures_cron_with_timezone(self):
        with patch.object(scheduler, "add_job") as mock_add_job:
            with patch.object(scheduler, "start") as mock_start:
                with patch.object(type(scheduler), "running", new_callable=PropertyMock, return_value=False):
                    start_scheduler()

                mock_add_job.assert_called_once()
                args, kwargs = mock_add_job.call_args
                trigger = kwargs.get("trigger")
                self.assertEqual(kwargs.get("id"), "generar_seguimientos_8am")
                self.assertEqual(kwargs.get("replace_existing"), True)
                self.assertEqual(str(trigger.timezone), settings.BUSINESS_TIMEZONE)


if __name__ == "__main__":
    unittest.main()
