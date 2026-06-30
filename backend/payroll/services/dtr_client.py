import requests
from django.conf import settings


class DTRClient:
    """
    Handles all HTTP communication with the DTR system.
    """

    def __init__(self):
        self.base_url = settings.DTR_API_BASE_URL
        self.headers = {'x-api-key': settings.DTR_API_KEY}

    def get_workers(self):
        """GET /api/payroll-export/workers"""
        resp = requests.get(
            f"{self.base_url}/workers",
            headers=self.headers,
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def update_worker_rates(self, dtr_id, data):
        """
        PUT /api/payroll-export/workers/:id
        Updates worker rates in DTR.
        """
        resp = requests.put(
            f"{self.base_url}/workers/{dtr_id}",
            headers=self.headers,
            json=data,
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def get_timesheet(self, start_date, end_date, employee_id=None):
        """GET /api/payroll-export/timesheet"""
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

    def get_salary(self, dtr_id, start_date, end_date):
        """
        GET /api/payroll-export/salary
        Uses DTR's own salaryCalculator to get gross pay.
        """
        params = {
            'employeeId': dtr_id,
            'start': start_date,
            'end': end_date,
        }
        resp = requests.get(
            f"{self.base_url}/salary",
            headers=self.headers,
            params=params,
            timeout=15
        )
        resp.raise_for_status()
        return resp.json()

    def mark_paid(self, shift_ids):
        """
        POST /api/payroll-export/mark-paid
        Marks specific shifts as paid in DTR by shift ID.
        """
        resp = requests.post(
            f"{self.base_url}/mark-paid",
            headers=self.headers,
            json={'shiftIds': shift_ids},
            timeout=15
        )
        resp.raise_for_status()
        return resp.json()