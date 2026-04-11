from django.db import models


class EmailVerificationCode(models.Model):
    """Email verification code with expiration and one-time usage semantics."""

    PURPOSE_LOGIN = 'login'
    PURPOSE_RESET_PASSWORD = 'reset_password'
    PURPOSE_CHOICES = [
        (PURPOSE_LOGIN, 'Login'),
        (PURPOSE_RESET_PASSWORD, 'Reset Password'),
    ]

    email = models.EmailField(db_index=True)
    code_hash = models.CharField(max_length=255)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default=PURPOSE_LOGIN)
    expires_at = models.DateTimeField(db_index=True)
    used_at = models.DateTimeField(null=True, blank=True, db_index=True)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['email', 'purpose', '-created_at']),
            models.Index(fields=['email', 'purpose', 'used_at', 'expires_at']),
        ]

    def __str__(self):
        return f"{self.email} ({self.purpose})"
