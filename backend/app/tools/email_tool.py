\"\"\"
Email Tool
Supports local database-backed email logs, SMTP sending, and Google Gmail API placeholders.
\"\"\"
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.email import EmailLog
from app.config import settings
from app.utils.logger import logger

class EmailTool:
    \"\"\"
    Manages email drafting, sending, and mock retrieval.
    Offers SMTP sending when credentials are provided in settings/env.
    Includes Gmail OAuth integration placeholders.
    \"\"\"

    def __init__(self, db: AsyncSession, user_id: uuid.UUID):
        self.db = db
        self.user_id = user_id

    async def list_emails(self, folder: str = "inbox") -> List[Dict[str, Any]]:
        \"\"\"Lists incoming or sent emails.\"\"\"
        try:
            # --- Google Gmail API Sync Placeholder ---
            # if settings.google_client_id and settings.google_client_secret:
            #     # TODO: Connect to Gmail API: service = build('gmail', 'v1', credentials=creds)
            #     # messages = service.users().messages().list(userId='me', q=folder).execute()
            #     # return messages.get('messages', [])
            #     pass

            if folder == "sent":
                stmt = select(EmailLog).where(EmailLog.user_id == self.user_id).order_by(EmailLog.sent_at.desc())
                result = await self.db.execute(stmt)
                logs = result.scalars().all()
                return [
                    {
                        "id": str(log.id),
                        "to": log.to_address,
                        "subject": log.subject,
                        "body": log.body,
                        "sent_at": log.sent_at.isoformat(),
                        "status": log.status
                    }
                    for log in logs
                ]

            # Mock Inbox
            return [
                {
                    "id": "mock-email-1",
                    "from": "manager@company.com",
                    "subject": "Q3 Project Alignment",
                    "body": "Hi, please make sure we align on the Q3 voice agent milestones by Friday.",
                    "received_at": datetime.utcnow().isoformat()
                },
                {
                    "id": "mock-email-2",
                    "from": "newsletter@techcrunch.com",
                    "subject": "AI Agent Startups Funding Surge",
                    "body": "The latest weekly digest of funding rounds in the speech synthesis and multi-agent domain.",
                    "received_at": datetime.utcnow().isoformat()
                }
            ]
        except Exception as e:
            logger.error("email_list_failed", user_id=self.user_id, error=str(e))
            return [{"error": f"Failed to list emails: {str(e)}"}]

    async def send_email(
        self,
        to_address: str,
        subject: str,
        body: str,
        draft: bool = False
    ) -> Dict[str, Any]:
        \"\"\"Sends an email or saves it as a draft.\"\"\"
        try:
            status = "draft" if draft else "sent"
            
            # Create a log entry in local PostgreSQL database
            log = EmailLog(
                user_id=self.user_id,
                to_address=to_address,
                subject=subject,
                body=body,
                status=status
            )
            self.db.add(log)
            await self.db.commit()
            await self.db.refresh(log)

            if draft:
                return {
                    "status": "success",
                    "message": f"Draft saved successfully (ID: {log.id})",
                    "email_id": str(log.id)
                }

            # Attempt real SMTP sending if config values exist (using environment fallbacks)
            smtp_host = settings.secret_key  # placeholder lookup or similar
            # For this agent system, if a user configures standard SMTP envs, we use them
            import os
            smtp_server = os.getenv("SMTP_SERVER")
            smtp_port = os.getenv("SMTP_PORT")
            smtp_username = os.getenv("SMTP_USERNAME")
            smtp_password = os.getenv("SMTP_PASSWORD")

            if smtp_server and smtp_port and smtp_username and smtp_password:
                try:
                    msg = MIMEMultipart()
                    msg['From'] = smtp_username
                    msg['To'] = to_address
                    msg['Subject'] = subject
                    msg.attach(MIMEText(body, 'plain'))

                    # Run sync SMTP call in executor or standard asyncio thread pool
                    import asyncio
                    def sync_send():
                        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                            server.starttls()
                            server.login(smtp_username, smtp_password)
                            server.send_message(msg)
                    
                    await asyncio.to_thread(sync_send)
                    logger.info("smtp_email_sent_successfully", to=to_address)
                    return {
                        "status": "success",
                        "message": f"Email successfully sent to {to_address}",
                        "email_id": str(log.id)
                    }
                except Exception as smtp_err:
                    logger.warning("smtp_sending_failed", error=str(smtp_err))
                    log.status = "failed"
                    await self.db.commit()
                    return {
                        "status": "partial_success",
                        "message": f"Saved email log but failed to deliver via SMTP: {str(smtp_err)}",
                        "email_id": str(log.id)
                    }

            # If no SMTP setup, we perform a successful mock send
            logger.info("mock_email_sent", to=to_address, subject=subject)
            return {
                "status": "success",
                "message": f"Email simulated and sent successfully to {to_address} (Mock Mode)",
                "email_id": str(log.id)
            }

        except Exception as e:
            logger.error("email_send_failed", user_id=self.user_id, error=str(e))
            return {"status": "error", "message": f"Failed to send email: {str(e)}"}
