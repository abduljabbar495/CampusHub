import base64
import hashlib

from cryptography.fernet import Fernet
from django.conf import settings


def _fernet():
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.FIELD_ENCRYPTION_KEY.encode()).digest())
    return Fernet(key)


def encrypt(text):
    return _fernet().encrypt(text.encode()).decode() if text else ""


def decrypt(token):
    return _fernet().decrypt(token.encode()).decode() if token else ""
