import random
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def generate_otp():
    # Generate a 4-digit OTP
    return str(random.randint(1000, 9999))

def send_otp_email(email, otp):
    subject = 'Your OTP for Password Reset'
    message = f'Your OTP is: {otp}'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]

    try:
        logger.info(f"Attempting to send OTP to {email} from {email_from}.")
        send_mail(subject, message, email_from, recipient_list)
        logger.info(f"OTP sent to {email} successfully.")
    except Exception as e:
        logger.error(f"Failed to send OTP to {email}. Error: {e}")