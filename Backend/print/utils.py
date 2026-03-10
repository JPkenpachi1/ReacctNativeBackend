# utils.py
import requests
from rest_framework_simplejwt.tokens import RefreshToken
from typing import Optional
from django.http import HttpRequest
from django.db.models.fields.files import FieldFile


def get_tokens_for_user(user):
    refresh = RefreshToken()
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


def absolute_file_url(
    request: Optional['HttpRequest'],
    file_field: Optional['FieldFile']
) -> Optional[str]:
    if not file_field:
        return None
    url = file_field.url
    return request.build_absolute_uri(url) if request else url


def send_expo_push_notification(expo_token: str, title: str, body: str, data: dict = {}):
    if not expo_token or not expo_token.startswith("ExponentPushToken"):
        print(f"❌ Invalid token: {expo_token}")
        return
    payload = {
        "to": expo_token,
        "title": title,
        "body": body,
        "data": data,
        "sound": "default",
    }
    try:
        response = requests.post(
            "https://exp.host/--/api/v2/push/send",
            json=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            timeout=5,
        )
        print(f"✅ Push response: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Push failed: {e}")


def notify_user(
    user,
    title: str,
    message: str,
    notification_type: str,
    order_id: int = None
):
    from .models import Notification, UserPushToken  # inside function = no circular import

    Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        related_order_id=order_id,
    )
    for push_token in UserPushToken.objects.filter(user=user):
        send_expo_push_notification(
            push_token.token, title, message, {"order_id": order_id}
        )
