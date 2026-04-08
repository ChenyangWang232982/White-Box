from django.conf import settings
from django.core.mail import send_mail


def email_verification_code(email, code, purpose='login'):
    """Send verification code email for login or password reset."""
    purpose_label = 'login' if purpose == 'login' else 'password reset'
    subject = 'WhiteBox verification code'
    body = (
        f"Your WhiteBox {purpose_label} code is: {code}\n"
        "This code will expire in 5 minutes.\n"
        "If you did not request this code, please ignore this email."
    )
    return send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )