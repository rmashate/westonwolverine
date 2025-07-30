"""Send the weekly digest to subscribers via Brevo.

This script loads subscriber emails from Supabase and sends the generated
`output/weekly_digest.md` content using Brevo's transactional API.
"""

import os
from pathlib import Path
from typing import List

import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")


def get_subscribers() -> List[str]:
    """Return list of subscriber email addresses from Supabase."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError("Supabase credentials are not configured")
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    resp = client.table("subscribers").select("email").execute()
    emails = [row["email"] for row in resp.data]
    return emails


def load_digest() -> str:
    """Load the Markdown digest file as a string."""
    path = Path(__file__).parent / "output" / "weekly_digest.md"
    if not path.exists():
        raise FileNotFoundError("Digest file not found. Run generate_digest.py first.")
    return path.read_text()


def send_email(to_email: str, subject: str, content: str) -> None:
    """Send the email via Brevo transactional API."""
    if not BREVO_API_KEY:
        raise RuntimeError("Brevo API key not configured")
    data = {
        "sender": {"name": "Weston Wolverine", "email": "noreply@example.com"},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": f"<pre>{content}</pre>",
    }
    headers = {"api-key": BREVO_API_KEY, "Content-Type": "application/json"}
    r = requests.post("https://api.brevo.com/v3/smtp/email", json=data, headers=headers, timeout=30)
    r.raise_for_status()


def main() -> None:
    digest = load_digest()
    subject = "Your Weston Wolverine Brief"
    for email in get_subscribers():
        send_email(email, subject, digest)
        print(f"Sent digest to {email}")


if __name__ == "__main__":
    main()
