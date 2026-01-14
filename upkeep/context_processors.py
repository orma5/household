from .models import Location

def active_location(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'profile') or not request.user.profile.account:
        return {}

    user_locations = Location.objects.filter(account=request.user.profile.account).order_by("-default", "name")
    
    if not user_locations.exists():
        return {"user_locations": [], "active_location": None}

    active_location_id = request.session.get("active_location_id")
    active_location = None

    if active_location_id:
        try:
            active_location = user_locations.get(pk=active_location_id)
        except Location.DoesNotExist:
            # Session has an ID but it's not valid for this user anymore
            pass

    if not active_location:
        # Fallback to default or first
        active_location = user_locations.first()
        # Update session so it persists
        request.session["active_location_id"] = active_location.id

    return {
        "user_locations": user_locations,
        "active_location": active_location,
        "account": request.user.profile.account,
    }
