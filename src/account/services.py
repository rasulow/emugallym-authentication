from django.core.mail import EmailMessage
from django.conf import settings
from os import environ as env
from dotenv import load_dotenv
import requests
from auth.logging_config import logger

load_dotenv()

ZENDER_API_KEY = env['ZENDER_API_KEY']
ZENDER_SENDER_ID = env['ZENDER_SENDER_ID']
ZENDER_BASE_URL = "https://salebot.demo.zoomnearby.com/api"


def send_sms(phone_number: str, code: str) -> bool:
    try:
        data = {
            "secret": ZENDER_API_KEY,
            "mode": "devices",
            "phone": phone_number,
            "message": f"Your verification code is: {code}",
            "sim": 1,
            "device": ZENDER_SENDER_ID
        }

        response = requests.post(
            f'{ZENDER_BASE_URL}/send/sms',
            data=data,
            verify=False
        )

        logger.info(f"SMS sending response: status={response.status_code}, body={response.text}")

        if response.status_code != 200:
            logger.warning(f"HTTP error while sending SMS: {response.status_code}")
            return False

        response_data = response.json()
        if response_data.get('status') != 200:
            logger.error(f"Zender API error: {response_data.get('message', 'Unknown error')}")
            return False

        logger.info(f"SMS successfully sent to {phone_number}")
        return True

    except requests.exceptions.RequestException as e:
        logger.exception(f"RequestException while sending SMS via Zender: {str(e)}")
        return False


def send_email(to: list[str], code: str) -> bool:
    try:
        email = EmailMessage(
            subject="Registration Confirmation",
            body=f"{code}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=to
        )
        email.send(fail_silently=False)
        logger.info(f"Email successfully sent to: {to}")
        return True
    except Exception as e:
        logger.exception(f"Error sending email: {e}")
        return False
