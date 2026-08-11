from common.models import get_account

from .models import Location


def get_active_location(request):
    """Resolve the location the request should operate on.

    Prefers `session["active_location_id"]`, but only when that location still
    belongs to the user's account — a stale id (deleted location, or a switched
    account) falls back to the account default rather than silently matching
    nothing. The resolved fallback is written back to the session so the choice
    is stable across requests.

    Returns None when the user has no account or no locations yet.
    """
    account = get_account(request.user)
    if not account:
        return None

    locations = Location.objects.filter(account=account).order_by("-default", "name")

    location_id = request.session.get("active_location_id")
    if location_id:
        location = locations.filter(pk=location_id).first()
        if location:
            return location

    location = locations.first()
    if location:
        request.session["active_location_id"] = location.id
    return location
