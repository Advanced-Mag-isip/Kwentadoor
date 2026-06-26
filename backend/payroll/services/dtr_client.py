import requests
from django.conf import settings


class DTRClient:
    """
    Handles all HTTP communication with the DTR system.
    All methods return raw parsed JSON from DTR.
    """

    def __init__(self):
        self.base_url = settings.DTR_API_BASE_URL
        self.headers = {'x-api-key': settings.DTR_API_KEY}

    def get_workers(self):
        """
        GET /api/payroll-export/workers
        Returns list of all active employees with their rates.
        """
        resp = requests.get(
            f"{self.base_url}/workers",
            headers=self.headers,
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def get_timesheet(self, start_date, end_date, employee_id=None):
        """
        GET /api/payroll-export/timesheet?start=&end=
        Returns shift records for all workers in the given period.
        Optionally filter by a single employee's DTR integer id.
        """
        params = {'start': start_date, 'end': end_date}
        if employee_id:
            params['employeeId'] = employee_id

        resp = requests.get(
            f"{self.base_url}/timesheet",
            headers=self.headers,
            params=params,
            timeout=15
        )
        resp.raise_for_status()
        return resp.json()