from langchain_core.tools import tool
from pydantic import BaseModel
from datetime import datetime
from src.my_agent.utils.gmail import schedule_meeting, send_gmail, check_calendar_availability

# Agent tools 
@tool
def write_email(to: str, subject: str, content: str) -> str:
    """Write and send an email via Gmail API."""
    send_gmail(to, subject, content)
    return f"Email sent to {to}"

@tool
def schedule_meeting_tool(
    attendees: list[str],
    subject: str,
    duration_minutes: int,
    preferred_day: datetime,
    start_time: int,
) -> str:
    """Schedule a meeting in Google Calendar."""
    return schedule_meeting(
        attendees=attendees,
        subject=subject,
        duration_minutes=duration_minutes,
        preferred_day=preferred_day,
        start_time=start_time,
    )

@tool
def calendar_freebusy(day: str) -> str:
    """Return busy slots for the given day."""
    return check_calendar_availability(day)

@tool
class Question(BaseModel):
      """Question to ask user."""
      content: str
    
@tool
class Done(BaseModel):
      """E-mail has been sent."""
      done: bool
      
    