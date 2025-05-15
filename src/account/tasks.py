from celery import shared_task
from account import services

@shared_task
def send_sms_async(phone_number, code):
    try:
        services.send_sms(phone_number, code)
        return f"SMS sent to {phone_number} with code {code}"
    except Exception as e:
        return str(e)
