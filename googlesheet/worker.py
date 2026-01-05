import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from googlesheet.config import SCOPE, SHEET_URL

import os
from dotenv import load_dotenv
load_dotenv()

service_account_info = json.loads(
    os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
)

def get_worksheet(name="Op-Cartage", sheet_url=SHEET_URL, scope=SCOPE):
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        service_account_info,
        scope,
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_url(sheet_url)
    return spreadsheet.worksheet(name)


class GoogleSheetClientLite:
    def __init__(self, sheet_url=SHEET_URL, scope=SCOPE):
        self._sheet_url = sheet_url
        self._scope = scope
        self._client = None
        self._sheet = None

    def _ensure(self):
        if self._sheet is None:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                service_account_info,
                self.scope,
            )
            self._client = gspread.authorize(creds)
            self._sheet = self._client.open_by_url(self._sheet_url)

    def get_worksheet(self, name):
        if not name:
            raise ValueError("name is required")
        self._ensure()
        return self._sheet.worksheet(name)

FIELDS = ["CTN NUMBER", "Depot", "Shipping Line", "Empty Park", "Last Dention"]

def get_records_by_ctn_numbers(ctn_numbers, name="Op-Cartage", fields=FIELDS):
    if not ctn_numbers:
        return []
    ws = get_worksheet(name)
    rows = ws.get_all_records()
    wanted = {str(x).strip() for x in ctn_numbers if x is not None}
    result = []
    for row in rows:
        ctn_value = str(row.get("CTN NUMBER", "")).strip()
        if ctn_value in wanted:
            result.append({field: row.get(field) for field in fields})
    return result


if __name__ == "__main__":
    print(get_records_by_ctn_numbers(["OOLU9505407", "GCXU5632435"]))
