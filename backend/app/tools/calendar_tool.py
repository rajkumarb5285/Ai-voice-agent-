\"\"\"
Calendar Tool
Integrates with local PostgreSQL calendar events and provides a Google Calendar OAuth boilerplate.
\"\"\"
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from app.models.calendar_event import CalendarEvent
from app.config import settings
from app.utils.logger import logger

# Google Calendar API Imports (Placeholder for integration)
# from googleapiclient.discovery import build
# from google.oauth2.credentials import Credentials

class CalendarTool:
    \"\"\"
    Manages calendar events.
    Supports local DB-backed calendar for out-of-the-box usage.
    Provides scaffolding/TODOs for Google Calendar sync.
    \"\"\"
    
    def __init__(self, db: AsyncSession, user_id: uuid.UUID):
        self.db = db
        self.user_id = user_id

    async def list_events(self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        \"\"\"Lists calendar events within a time range.\"\"\"
        try:
            # --- Google Calendar Sync Placeholder ---
            # if settings.google_client_id and settings.google_client_secret:
            #     # TODO: Fetch access token from user credentials/profile in DB
            #     # creds = Credentials(token=access_token, refresh_token=refresh_token, client_id=settings.google_client_id, client_secret=settings.google_client_secret)
            #     # service = build('calendar', 'v3', credentials=creds)
            #     # gcal_events = service.events().list(calendarId='primary', timeMin=start_time.isoformat() + 'Z').execute()
            #     # return gcal_events.get('items', [])
            #     pass

            # Local DB Fallback (Always active)
            stmt = select(CalendarEvent).where(CalendarEvent.user_id == self.user_id)
            if start_time:
                stmt = stmt.where(CalendarEvent.start_time >= start_time)
            if end_time:
                stmt = stmt.where(CalendarEvent.end_time <= end_time)
            
            stmt = stmt.order_by(CalendarEvent.start_time)
            result = await self.db.execute(stmt)
            events = result.scalars().all()

            return [
                {
                    "id": str(e.id),
                    "title": e.title,
                    "description": e.description,
                    "location": e.location,
                    "start_time": e.start_time.isoformat(),
                    "end_time": e.end_time.isoformat(),
                    "is_all_day": e.is_all_day,
                    "source": "local_db" if not e.gcal_event_id else "google_calendar"
                }
                for e in events
            ]

        except Exception as e:
            logger.error("calendar_list_events_failed", user_id=self.user_id, error=str(e))
            return [{"error": f"Failed to retrieve calendar events: {str(e)}"}]

    async def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        is_all_day: bool = False
    ) -> Dict[str, Any]:
        \"\"\"Creates a new calendar event.\"\"\"
        try:
            # Local DB creation
            event = CalendarEvent(
                user_id=self.user_id,
                title=title,
                description=description,
                location=location,
                start_time=start_time,
                end_time=end_time,
                is_all_day=is_all_day
            )
            self.db.add(event)
            await self.db.commit()
            await self.db.refresh(event)

            # --- Google Calendar Sync Placeholder ---
            # if settings.google_client_id and settings.google_client_secret:
            #     # TODO: Authenticate service & insert event
            #     # gcal_event = { 'summary': title, 'description': description, ... }
            #     # created = service.events().insert(calendarId='primary', body=gcal_event).execute()
            #     # event.gcal_event_id = created['id']
            #     # await self.db.commit()
            #     pass

            logger.info("calendar_event_created", event_id=event.id, title=title)
            return {
                "status": "success",
                "message": f"Event '{title}' scheduled for {start_time.strftime('%Y-%m-%d %H:%M')}",
                "event": {
                    "id": str(event.id),
                    "title": event.title,
                    "start_time": event.start_time.isoformat(),
                    "end_time": event.end_time.isoformat()
                }
            }
        except Exception as e:
            logger.error("calendar_create_event_failed", user_id=self.user_id, error=str(e))
            return {"status": "error", "message": f"Failed to create event: {str(e)}"}

    async def delete_event(self, event_id_str: str) -> Dict[str, Any]:
        \"\"\"Deletes an event from the calendar.\"\"\"
        try:
            event_id = uuid.UUID(event_id_str)
            stmt = select(CalendarEvent).where(
                and_(CalendarEvent.id == event_id, CalendarEvent.user_id == self.user_id)
            )
            res = await self.db.execute(stmt)
            event = res.scalar_one_or_none()

            if not event:
                return {"status": "error", "message": "Event not found."}

            # --- Google Calendar Delete Placeholder ---
            # if event.gcal_event_id and settings.google_client_id:
            #     # TODO: Delete from GCal: service.events().delete(calendarId='primary', eventId=event.gcal_event_id).execute()
            #     pass

            await self.db.delete(event)
            await self.db.commit()
            
            logger.info("calendar_event_deleted", event_id=event_id_str)
            return {"status": "success", "message": f"Event deleted successfully."}

        except Exception as e:
            logger.error("calendar_delete_event_failed", event_id=event_id_str, error=str(e))
            return {"status": "error", "message": f"Failed to delete event: {str(e)}"}
