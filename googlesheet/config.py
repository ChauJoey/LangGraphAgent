import os

# Google Sheets API scopes.
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]

# Replace with your spreadsheet URL or set SHEET_URL env var.
SHEET_URL = os.environ.get(
    "SHEET_URL",
    "https://docs.google.com/spreadsheets/d/1nZ8_RLmKoAQNhreIVq7WRHMlVPua-ty6zpZP5mTYbNM/edit?gid=1676080520#gid=1676080520",
)
