from __future__ import annotations

import os.path
from datetime import datetime, timedelta, time, timezone
from typing import List

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dateutil import tz
from google.auth.transport.requests import Request

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz

import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import base64
from email.mime.text import MIMEText
# OAuth scope – full read/write access to the user’s calendars.
SCOPES = ["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/gmail.send"]

def get_calendar_service():
    """Return an authenticated googleapiclient discovery Resource for Calendar v3."""
    creds: Credentials | None = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # Refresh or initiate auth if necessary
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds, cache_discovery=False)

def schedule_meeting(
    attendees: List[str],
    subject: str,
    duration_minutes: int,
    preferred_day: datetime,
    start_time: int,
    *,
    calendar_id: str = "primary",
    timezone_str: str = "Australia/Melbourne",
) -> str:
    """
    Create a Google Calendar event.

    Args:
        attendees: list of attendee e-mail addresses.
        subject:   event title (summary).
        duration_minutes: meeting length in minutes.
        preferred_day:   date component (year-month-day). The time part is ignored.
        start_time: hour of day in 24-h local time (e.g. 14 -> 2 pm).
        calendar_id: target calendar (default 'primary').
        timezone_str: IANA time-zone string for start/end.

    Returns:
        The event’s HTML link (str).
    """
    # Combine date + hour and make it tz-aware
    tzinfo = tz.gettz(timezone_str)
    start_dt = datetime.combine(preferred_day.date(), time(start_time, 0, 0), tzinfo)
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    event_body = {
        "summary": subject,
        "start": {
            "dateTime": start_dt.isoformat(),
            "timeZone": timezone_str,
        },
        "end": {
            "dateTime": end_dt.isoformat(),
            "timeZone": timezone_str,
        },
        "attendees": [{"email": addr} for addr in attendees],
        # Optional: email all participants so the invite shows up in their inbox
        "guestsCanModify": False,
    }

    service = get_calendar_service()
    created = (
        service.events()
        .insert(
            calendarId=calendar_id,
            body=event_body,
            sendUpdates="all",  # notifications: 'all', 'externalOnly', or 'none'
        )
        .execute()
    )

    return created.get("htmlLink", created.get("id"))

def check_calendar_availability(day: str) -> str:
    """Returns free/busy times for the given day using Google Calendar FreeBusy API."""
    
    # Authenticate with Google Calendar API
    creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/calendar.readonly'])
    service = build('calendar', 'v3', credentials=creds)

    # Set timezone
    timezone = pytz.timezone("Australia/Melbourne")  # Change if needed

    # Define time range for the entire day
    start_of_day = timezone.localize(datetime.strptime(day, "%Y-%m-%d"))
    end_of_day = start_of_day + timedelta(days=1)

    # Build FreeBusy query
    body = {
        "timeMin": start_of_day.isoformat(),
        "timeMax": end_of_day.isoformat(),
        "timeZone": timezone.zone,
        "items": [{"id": "primary"}],
    }

    # Call the freebusy.query API
    freebusy_result = service.freebusy().query(body=body).execute()

    # Extract busy periods
    busy_times = freebusy_result["calendars"]["primary"].get("busy", [])

    # If no busy times, user is free
    if not busy_times:
        return "Free all day"

    # Otherwise, return busy slots
    busy_slots = []
    for slot in busy_times:
        start = slot["start"]
        end = slot["end"]
        busy_slots.append(f"{start} → {end}")

    return "Busy at:\n" + "\n".join(busy_slots)

def create_message(sender, to, subject, message_text):
  message = MIMEText(message_text)
  message['to'] = to
  message['from'] = sender
  message['subject'] = subject
  raw_message = base64.urlsafe_b64encode(message.as_string().encode("utf-8"))
  return {
    'raw': raw_message.decode("utf-8")
  }

def send_message(service, user_id, message):
  try:
    message = service.users().messages().send(userId=user_id, body=message).execute()
    print('Message Id: %s' % message['id'])
    return message
  except Exception as e:
    print('An error occurred: %s' % e)
    return None

#weird observation, adding a blank line bw the description and the args causes an issue
def send_gmail(recipient, subject, message_text):
    """Send an email using the Gmail API.
    Args:
        recipient: Email address of the recipient.
        subject: Subject of the email.
        message_text: Body of the email.
    """

    sender = "ahmad.pencil@gmail.com"  # hardcoded sender

    creds = None
    
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("gmail", "v1", credentials=creds)
        message_body = create_message(sender, recipient, subject, message_text)
        sent_message = send_message(service, "me", message_body)
        
        if sent_message:
            print("Email sent successfully!")
        else:
            print("Failed to send email.")

    except HttpError as error:
        print(f"An error occurred: {error}")
        
        
if __name__ == "__main__":
    
    print ("dfgdfg")
    
    day = "2025-07-12"
    availability = check_calendar_availability(day)
    print(availability)
    
    recipient = "ajam0033@student.monash.edu"
    subject = "Test Email from Gmail API"
    body = "Hello!\nThis email was sent using the Gmail API and Python."

    send_gmail(recipient, subject, body)
    
    link = schedule_meeting(
        attendees=["teammate@example.com", "boss@example.com"],
        subject="test meeting",
        duration_minutes=30,
        preferred_day=datetime(2025, 7, 14),  # YYYY-MM-DD
        start_time=16,  #
    )
    print("Meeting created:", link)
    
    
    