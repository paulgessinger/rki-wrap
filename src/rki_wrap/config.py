import os
import datetime
from dotenv import load_dotenv

load_dotenv()

SOURCE_URL = os.environ["SOURCE_URL"]
EXCEL_SOURCE_URL = os.environ["EXCEL_SOURCE_URL"]

SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
SQLALCHEMY_TRACK_MODIFICATIONS = False

DATE_WINDOW = datetime.timedelta(weeks=8)

HEALTHCHECK_URL = os.environ.get("HEALTHCHECK_URL")
