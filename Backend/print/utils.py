# utils.py - Create this file in your app directory
from rest_framework_simplejwt.tokens import RefreshToken

def get_tokens_for_user(user):
    """
    Generate JWT tokens for a user with custom claims.
    """
    refresh = RefreshToken()
    
    # Add custom claims
    refresh['user_id'] = user.id
    refresh['username'] = user.username
    refresh['role'] = user.role
    refresh['is_active'] = user.is_active
    refresh['is_suspended'] = user.is_suspended
    refresh['is_staff'] = user.is_staff
    
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }






from typing import Optional
from django.http import HttpRequest
from django.db.models.fields.files import FieldFile

def absolute_file_url(request: Optional['HttpRequest'], file_field: Optional['FieldFile']) -> Optional[str]:
    if not file_field:
        return None
    url = file_field.url  # e.g. /media/orders/2025/11/01/file.pdf
    return request.build_absolute_uri(url) if request else url







import requests

def send_expo_push_notification(expo_token: str, title: str, body: str, data: dict = {}):
    """Send a push notification via Expo Push API."""
    if not expo_token or not expo_token.startswith("ExponentPushToken"):
        return
    payload = {
        "to": expo_token,
        "title": title,
        "body": body,
        "data": data,
        "sound": "default",
    }
    try:
        requests.post(
            "https://exp.host/--/api/v2/push/send",
            json=payload,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=5,
        )
    except Exception:
        pass  # Don't crash order flow if push fails


def notify_user(user, title: str, message: str, notification_type: str, order_id: int = None):
    """Create in-app Notification + send Expo push to all user devices."""
    from .models import Notification, UserPushToken

    Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        related_order_id=order_id,
    )
    for push_token in UserPushToken.objects.filter(user=user):
        send_expo_push_notification(push_token.token, title, message, {"order_id": order_id})
