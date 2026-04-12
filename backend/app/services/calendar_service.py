"""
Google Calendar integration.
Creates daily prep blocks, task events, and syncs completion status.
"""
from datetime import datetime, date, timedelta, timezone
from typing import Optional
import httpx

CALENDAR_API = "https://www.googleapis.com/calendar/v3"


async def _auth_header(token_data: dict) -> dict:
    return {"Authorization": f"Bearer {token_data['access_token']}"}


async def refresh_google_token(token_data: dict, client_id: str, client_secret: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post("https://oauth2.googleapis.com/token", data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": token_data.get("refresh_token"),
            "grant_type": "refresh_token",
        })
        if resp.status_code == 200:
            new_data = resp.json()
            return {**token_data, "access_token": new_data["access_token"]}
    return token_data


async def create_prep_calendar(token_data: dict, calendar_name: str) -> Optional[str]:
    """Create a dedicated PlacementPrep calendar. Returns calendar ID."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{CALENDAR_API}/calendars",
                headers=await _auth_header(token_data),
                json={"summary": calendar_name, "description": "PlacementPrep AI — Your interview prep schedule", "timeZone": "Asia/Kolkata"},
            )
            if resp.status_code in (200, 201):
                return resp.json().get("id")
    except Exception:
        pass
    return None


async def create_daily_prep_block(
    token_data: dict,
    calendar_id: str,
    event_date: date,
    title: str,
    description: str,
    start_hour: int = 19,
    duration_hours: float = 1.5,
) -> Optional[str]:
    """Create a calendar event for a daily prep block. Returns event ID."""
    try:
        start_dt = datetime(event_date.year, event_date.month, event_date.day, start_hour, 0, tzinfo=timezone.utc)
        end_dt = start_dt + timedelta(hours=duration_hours)
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{CALENDAR_API}/calendars/{calendar_id}/events",
                headers=await _auth_header(token_data),
                json={
                    "summary": title,
                    "description": description,
                    "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Kolkata"},
                    "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Kolkata"},
                    "colorId": "9",  # Blueberry
                    "reminders": {
                        "useDefault": False,
                        "overrides": [
                            {"method": "popup", "minutes": 60},
                            {"method": "email", "minutes": 120},
                        ],
                    },
                },
            )
            if resp.status_code in (200, 201):
                return resp.json().get("id")
    except Exception:
        pass
    return None


async def create_interview_day_event(
    token_data: dict,
    calendar_id: str,
    interview_date: date,
    company: str,
    role: str,
) -> Optional[str]:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{CALENDAR_API}/calendars/{calendar_id}/events",
                headers=await _auth_header(token_data),
                json={
                    "summary": f"🎯 {company} {role} Interview — You're ready!",
                    "description": f"Your {company} {role} interview. You've prepared for this. Trust your preparation.",
                    "start": {"date": interview_date.isoformat()},
                    "end": {"date": interview_date.isoformat()},
                    "colorId": "11",  # Tomato red
                    "reminders": {
                        "useDefault": False,
                        "overrides": [
                            {"method": "popup", "minutes": 1440},  # 1 day before
                            {"method": "email", "minutes": 1440},
                        ],
                    },
                },
            )
            if resp.status_code in (200, 201):
                return resp.json().get("id")
    except Exception:
        pass
    return None


async def mark_event_complete(
    token_data: dict,
    calendar_id: str,
    event_id: str,
    original_title: str,
) -> bool:
    """Update event title to show ✓ completed."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{CALENDAR_API}/calendars/{calendar_id}/events/{event_id}",
                headers=await _auth_header(token_data),
                json={"summary": f"✓ {original_title}", "colorId": "2"},  # Sage green
            )
            return resp.status_code in (200, 201)
    except Exception:
        return False


async def bulk_create_prep_schedule(
    token_data: dict,
    calendar_id: str,
    start_date: date,
    end_date: date,
    company: str,
    role: str,
    daily_tasks_by_day: dict,  # {day_number: [task_title, ...]}
    daily_hours: float = 2.0,
) -> dict:
    """Create all prep events in one shot. Returns {day_number: event_id}."""
    event_ids = {}
    current = start_date
    day_num = 1
    while current <= end_date:
        tasks = daily_tasks_by_day.get(day_num, [])
        if tasks:
            desc = f"PlacementPrep for {company} {role}\n\nToday's tasks:\n" + "\n".join(f"• {t}" for t in tasks[:5])
            title = f"⚡ PlacementPrep — Day {day_num}"
            event_id = await create_daily_prep_block(
                token_data, calendar_id, current, title, desc,
                start_hour=19, duration_hours=daily_hours,
            )
            if event_id:
                event_ids[str(day_num)] = event_id
        current += timedelta(days=1)
        day_num += 1
    return event_ids
