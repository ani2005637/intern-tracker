#!/usr/bin/env python3
"""
Hosting Renewal Reminder Script

This script checks the 'hosting_details' collection in MongoDB for hosting accounts/domains
with renewal dates approaching in 1 month (default: 30 days). For any matching domains,
it generates an alert notification for all Admin users in the database and optionally
sends them an email if SMTP credentials are configured.

To prevent duplicate alerts, the script tracks sent notifications using metadata in MongoDB.

Usage:
    python hosting_reminder.py [--days 30] [--dry-run] [--simulated-date YYYY-MM-DD]
"""

import os
import sys
import datetime
import argparse
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pymongo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("hosting_reminder")


def get_db():
    """Establish connection to MongoDB Atlas."""
    mongo_uri = os.environ.get('MONGO_URI')
    if not mongo_uri:
        # Default connection string from app.py
        mongo_uri = 'mongodb+srv://srikakulaanirudh0506_db_user:e9gSM1PbSju6TYek@cluster0.3jbhs01.mongodb.net/?appName=Cluster0'
    
    logger.info("Connecting to MongoDB...")
    try:
        client = pymongo.MongoClient(mongo_uri)
        db = client['intern_tracker']
        # Simple ping to test connection
        client.admin.command('ping')
        logger.info("Successfully connected to MongoDB database: intern_tracker")
        return db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        sys.exit(1)


def parse_date(date_val):
    """Parse a date value from MongoDB (string or date object) into a datetime.date object."""
    if not date_val:
        return None
    if isinstance(date_val, (datetime.datetime, datetime.date)):
        return date_val.date() if isinstance(date_val, datetime.datetime) else date_val
    if isinstance(date_val, str):
        date_str = date_val.strip()
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"):
            try:
                return datetime.datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
    return None


def get_smtp_config():
    """Retrieve SMTP configuration from environment variables or parent config.json."""
    config = {
        "smtp_server": os.environ.get("SMTP_SERVER", "smtp.gmail.com"),
        "smtp_port": int(os.environ.get("SMTP_PORT", 587)),
        "sender": os.environ.get("SMTP_SENDER", ""),
        "password": os.environ.get("SMTP_PASSWORD", "")
    }

    # Try loading from bulk parent directory config.json if sender/password not in env
    if not config["sender"] or not config["password"]:
        parent_config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.json"))
        if os.path.exists(parent_config_path):
            try:
                import json
                with open(parent_config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if not config["sender"]:
                        config["sender"] = cfg.get("gmail_sender", "")
                    if not config["password"]:
                        config["password"] = cfg.get("gmail_app_password", "")
            except Exception as e:
                logger.warning(f"Could not load config.json for SMTP settings: {e}")

    return config


def send_email_alert(smtp_config, admin_emails, domain, renewal_date, client_email):
    """Send an email alert to the admin users."""
    if not smtp_config["sender"] or not smtp_config["password"]:
        logger.warning("SMTP sender or password not configured. Skipping email notification.")
        return False

    if not admin_emails:
        logger.warning("No admin email addresses found to send email alerts to.")
        return False

    subject = f"[Action Required] Hosting Renewal Reminder: {domain} is renewing on {renewal_date}"
    
    body = f"""Dear Admin,

This is an automated reminder alert.

The following hosting account/domain is scheduled for renewal in 1 month (or less):

- Domain/Account: {domain}
- Renewal Date: {renewal_date}
- Client/Associated Email: {client_email or 'Not Available'}

Please send a reminder email to the client to coordinate the hosting renewal.

Best regards,
Hosting Tracker Alert System
"""

    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_config["sender"]
        msg['To'] = ", ".join(admin_emails)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_config["smtp_server"], smtp_config["smtp_port"])
        server.starttls()
        server.login(smtp_config["sender"], smtp_config["password"])
        server.sendmail(smtp_config["sender"], admin_emails, msg.as_string())
        server.quit()
        logger.info(f"Email alert sent successfully to: {', '.join(admin_emails)}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Check hosting renewal dates and alert admins.")
    parser.add_argument("--days", type=int, default=30, help="Days before renewal to trigger alert (default: 30)")
    parser.add_argument("--dry-run", action="store_true", help="Print matches without saving notifications or sending emails")
    parser.add_argument("--simulated-date", type=str, help="Simulate today's date (format: YYYY-MM-DD) for testing")
    args = parser.parse_args()

    db = get_db()

    # Determine reference date (today)
    if args.simulated_date:
        try:
            today = datetime.datetime.strptime(args.simulated_date, "%Y-%m-%d").date()
            logger.info(f"Simulating today's date as: {today}")
        except ValueError:
            logger.error(f"Invalid simulated-date format: '{args.simulated_date}'. Use YYYY-MM-DD.")
            sys.exit(1)
    else:
        today = datetime.date.today()
        logger.info(f"Today's date: {today}")

    # Fetch admin users
    admins = list(db.users.find({"role": "Admin"}))
    if not admins:
        logger.warning("No Admin users found in the database. Notifications cannot be delivered.")
    
    admin_usernames = [admin['username'] for admin in admins]
    admin_emails = [admin['email'] for admin in admins if admin.get('email')]
    logger.info(f"Found {len(admins)} Admin user(s). Email recipients: {admin_emails}")

    # Fetch all hosting details
    # We scan all categories since renewal date might be present in any of them in the future
    hosting_records = list(db.hosting_details.find({}))
    logger.info(f"Retrieved {len(hosting_records)} total hosting records from database.")

    alerts_triggered = 0
    smtp_config = get_smtp_config()

    for record in hosting_records:
        domain = record.get('Domains')
        # Check potential renewal date fields (typically 'Renewal Date' or 'date')
        renewal_date_val = record.get('Renewal Date') or record.get('date')
        if not domain or not renewal_date_val:
            continue

        renewal_date = parse_date(renewal_date_val)
        if not renewal_date:
            continue

        # Calculate days until renewal
        delta = (renewal_date - today).days

        # We trigger alert if the renewal is coming up in <= target days and >= 0 days
        if 0 <= delta <= args.days:
            category = record.get('category', 'Unknown')
            client_email = record.get('Email') or ''
            renewal_date_str = renewal_date.strftime("%Y-%m-%d")

            logger.info(f"Match Found: '{domain}' ({category}) renewing on {renewal_date_str} (in {delta} days). Client Email: {client_email or 'None'}")
            
            # Check if this alert was already sent to prevent spam
            already_notified = False
            if not args.dry_run:
                existing_notif = db.notifications.find_one({
                    "type": "hosting_renewal_reminder",
                    "metadata.domain": domain,
                    "metadata.renewal_date": renewal_date_str
                })
                if existing_notif:
                    already_notified = True
                    logger.info(f"   [Skipped] Alert already recorded in database for {domain} on {renewal_date_str}")

            if already_notified:
                continue

            alerts_triggered += 1

            if args.dry_run:
                logger.info(f"   [Dry Run] Would send alert for domain: {domain}")
                continue

            # Create internal database notification for each admin
            notification_message = (
                f"Hosting Renewal Alert: The domain '{domain}' ({category}) is renewing on "
                f"{renewal_date_str} (in {delta} days). Remember to send a mail to the client email: {client_email or 'N/A'}."
            )

            for admin_user in admins:
                try:
                    db.notifications.insert_one({
                        "username": admin_user['username'],
                        "message": notification_message,
                        "type": "hosting_renewal_reminder",
                        "created_at": datetime.datetime.now(datetime.timezone.utc),
                        "read": False,
                        "metadata": {
                            "domain": domain,
                            "renewal_date": renewal_date_str,
                            "days_remaining": delta
                        }
                    })
                except Exception as ne:
                    logger.error(f"   Failed to insert notification for admin '{admin_user['username']}': {ne}")

            logger.info(f"   Created dashboard notification alerts for admins.")

            # Send email to admin users
            send_email_alert(smtp_config, admin_emails, domain, renewal_date_str, client_email)

    logger.info(f"Renewal check finished. Total alerts triggered: {alerts_triggered}")


if __name__ == '__main__':
    main()
