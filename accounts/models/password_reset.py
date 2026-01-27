"""
Password reset token model for secure password reset functionality.
"""
from django.db import models
from django.utils import timezone

from accounts.models import User


class PasswordResetToken(models.Model):
    """
    Temporary token for password reset requests.
    Tokens expire after 24 hours and are single-use.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
        help_text='User requesting password reset'
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text='Secure reset token'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='When token was created'
    )
    expires_at = models.DateTimeField(
        help_text='When token expires (24 hours from creation)'
    )
    used = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Whether token has been used'
    )
    
    class Meta:
        db_table = 'password_reset_tokens'
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['used', 'expires_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Password reset token for {self.user.email}'
    
    def is_valid(self):
        """Check if token is valid and not expired."""
        return (
            not self.used and
            timezone.now() < self.expires_at
        )
