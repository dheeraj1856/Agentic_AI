# email_agent.py


import os
from typing import Dict, Optional

import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To

from agents import Agent, function_tool


class SendGridClient:
    """
    Minimal wrapper so the tool stays tiny and easy to read.
    This also makes it straightforward to stub in tests if needed.
    """
    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or os.environ.get("SENDGRID_API_KEY")
        if not api_key:
            raise RuntimeError("SENDGRID_API_KEY is not set")
        self._client = sendgrid.SendGridAPIClient(api_key=api_key)

    def send_html_email(self, sender: str, recipient: str, subject: str, html_body: str) -> int:
        content = Content("text/html", html_body)
        mail = Mail(Email(sender), To(recipient), subject, content).get()
        response = self._client.client.mail.send.post(request_body=mail)
        return response.status_code


# Keep the same tool name and parameters so the output contract is identical.
@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """
    Send an email with the given subject and HTML body.
    NOTE: Update sender/recipient to your verified SendGrid identities if needed.
    """
    # In the original, these were literal. Keep that to preserve behavior.
    sender = "ed@edwarddonner.com"
    recipient = "ed.donner@gmail.com"

    status = SendGridClient().send_html_email(sender, recipient, subject, html_body)
    print("Email response", status)
    return {"status": "success"}


INSTRUCTIONS = (
    "You are able to send a nicely formatted HTML email based on a detailed report.\n"
    "You will be provided with a detailed report. You should use your tool to send one email, "
    "providing the report converted into clean, well presented HTML with an appropriate subject line."
)

# Public object name and configuration remain unchanged.
email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
