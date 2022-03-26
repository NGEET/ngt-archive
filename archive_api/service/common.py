
from archive_api.models import SERVICE_ACCOUNT_CHOICES


class ServiceAccountException(Exception):
    """Exception class for service accounts"""

    def __init__(self, msg: str, service: int):
        """Initialize Exception"""
        service = SERVICE_ACCOUNT_CHOICES[service][1]
        super().__init__(f"Service Account {service}: {msg}")


