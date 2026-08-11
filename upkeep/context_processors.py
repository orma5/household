from common.models import get_account

from .models import Location
from .selectors import get_active_location


def active_location(request):
    if not request.user.is_authenticated:
        return {}

    account = get_account(request.user)
    if not account:
        return {}

    return {
        "user_locations": Location.objects.filter(account=account).order_by(
            "-default", "name"
        ),
        "active_location": get_active_location(request),
        "account": account,
    }
