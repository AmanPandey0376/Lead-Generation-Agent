import os
import smtplib
import logging
import asyncio
from typing import Optional, List, Dict, Any
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

def _sync_verify_smtp() -> None:
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "ecommerce@vvsons.ae")
    password = os.getenv("SMTP_PASSWORD", "ecvn wqbh bbur fwcg")
    
    if not user or not password:
        raise ValueError("SMTP_USER and SMTP_PASSWORD environment variables are not set")
    
    # Mask password for logs
    masked_pw = password[:2] + "*" * (len(password) - 4) + password[-2:] if len(password) > 4 else "****"
    logger.info(f"Connecting to SMTP server {host}:{port} as {user} with password {masked_pw}")
    
    server = smtplib.SMTP(host, port, timeout=10)
    try:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(user, password)
    finally:
        try:
            server.quit()
        except Exception:
            pass


async def verify_smtp_connection() -> Dict[str, Any]:
    """
    Tests SMTP connection and credentials.
    """
    try:
        await asyncio.to_thread(_sync_verify_smtp)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"SMTP connection check failed: {e}")
        return {"status": "error", "message": str(e)}


def _sync_send_email(to_email: str, subject: str, text_body: str, html_body: Optional[str] = None) -> None:
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "ecommerce@vvsons.ae")
    password = os.getenv("SMTP_PASSWORD", "ecvn wqbh bbur fwcg")
    from_email = os.getenv("SMTP_FROM", user)
    
    if not user or not password:
        raise ValueError("SMTP_USER and SMTP_PASSWORD environment variables are not set")
        
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    
    # Attach plain text
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    
    # Attach HTML if provided
    if html_body:
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        
    server = smtplib.SMTP(host, port, timeout=10)
    try:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(user, password)
        server.sendmail(from_email, [to_email], msg.as_string())
    finally:
        try:
            server.quit()
        except Exception:
            pass


async def send_email(to_email: str, subject: str, text_body: str, html_body: Optional[str] = None) -> Dict[str, Any]:
    """
    Sends a single email asynchronously.
    """
    try:
        if not to_email or "@" not in to_email:
            raise ValueError(f"Invalid email address: {to_email}")
            
        await asyncio.to_thread(_sync_send_email, to_email, subject, text_body, html_body)
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return {"success": False, "error": str(e)}


async def send_bulk_email(leads: List[Dict[str, Any]], subject: str, body: str, delay: float = 2.0) -> Dict[str, Any]:
    """
    Sends emails to multiple leads one by one with a controlled delay.
    """
    results = []
    sent_count = 0
    failed_count = 0
    
    for lead in leads:
        to_email = lead.get("email")
        if not to_email or "@" not in to_email:
            results.append({"lead_id": lead.get("id"), "success": False, "error": "Invalid/Empty email"})
            failed_count += 1
            continue
            
        # Replace placeholders
        lead_subject = subject.replace("{name}", lead.get("name") or "").replace("{company}", lead.get("company") or "").replace("{title}", lead.get("title") or "")
        lead_body = body.replace("{name}", lead.get("name") or "").replace("{company}", lead.get("company") or "").replace("{title}", lead.get("title") or "")
        
        res = await send_email(to_email, lead_subject, lead_body)
        results.append({"lead_id": lead.get("id"), "success": res["success"], "error": res.get("error")})
        if res["success"]:
            sent_count += 1
        else:
            failed_count += 1
            
        await asyncio.sleep(delay)
        
    return {
        "processed": len(leads),
        "sent": sent_count,
        "failed": failed_count,
        "results": results
    }
