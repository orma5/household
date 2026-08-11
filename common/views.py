from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone
from django.views.static import serve

from upkeep.models import Item, Task
from upkeep.selectors import get_active_location

from .models import Profile, get_account


def _may_access_upload(user, path):
    """Whether `user` is entitled to the upload stored at `path`.

    Uploads are matched back to the row that owns them; anything no row claims
    is treated as non-existent.
    """
    # Your own picture, which you can have before joining a household.
    if Profile.objects.filter(user=user, profile_picture=path).exists():
        return True

    account = get_account(user)
    if not account:
        # Location.account and Profile.account are both nullable, so filtering
        # on account=None would match orphaned rows rather than nothing.
        return False

    return (
        Item.objects.filter(receipt_file=path, location__account=account).exists()
        or Profile.objects.filter(profile_picture=path, account=account).exists()
    )


@login_required
def serve_upload(request, path):
    """Serve a user upload, scoped to the account that owns it.

    Authentication alone is not enough here: Django only appends a random
    suffix to an uploaded filename when it collides, so `receipts/receipt.pdf`
    is guessable and any logged-in user of any household could fetch it.

    404 rather than 403 on refusal, so this does not confirm which paths exist.
    """
    if not _may_access_upload(request.user, path):
        raise Http404("No such file")
    return serve(request, path, document_root=settings.MEDIA_ROOT)


@login_required
def home(request):
    account = get_account(request.user)
    if not account:
        return render(request, "home.html", {"no_account": True})

    active_location = get_active_location(request)

    context = {}


    if active_location:
        today = timezone.now().date()
        week_from_now = today + timedelta(days=7)
        month_end = today + timedelta(days=30)

        # --- Filter Base QuerySets ---
        # Only ACTIVE items for inventory stats
        items = Item.objects.filter(location=active_location, status=Item.ItemStatus.ACTIVE)
        # All items for broken counts
        all_loc_items = Item.objects.filter(location=active_location)
        # Tasks linked to items in this location
        tasks = Task.objects.filter(item__location=active_location)

        # --- Widget 1: Action Center ---
        # Overdue: next_due_date < today AND not snoozed into future
        overdue_tasks_count = tasks.filter(
            Q(next_due_date__lt=today) & 
            (Q(snoozed_until__isnull=True) | Q(snoozed_until__lt=today))
        ).count()

        tasks_due_this_week = tasks.filter(
            Q(next_due_date__lte=week_from_now) & 
            (Q(snoozed_until__isnull=True) | Q(snoozed_until__lte=week_from_now))
        ).count()

        broken_items_count = all_loc_items.filter(status=Item.ItemStatus.BROKEN).count()

        # --- Widget 2: Asset & Value ---
        total_active_items = items.count()
        total_asset_value = items.aggregate(Sum('purchase_value'))['purchase_value__sum'] or 0
        
        warranty_threshold = today + timedelta(days=60)
        warranty_watch = items.filter(
            warranty_expiration__gte=today,
            warranty_expiration__lte=warranty_threshold
        ).order_by('warranty_expiration')[:5]

        # --- Widget 3: Workload Forecast ---
        # Estimate hours for tasks due in the next 30 days
        monthly_tasks = tasks.filter(next_due_date__range=[today, month_end])
        maintenance_load = monthly_tasks.aggregate(Sum('estimated_hours_to_complete'))['estimated_hours_to_complete__sum'] or 0
        
        # Next tasks (including overdue ones at the top)
        next_up_tasks = tasks.order_by('next_due_date')[:5]

        # --- Widget 4: Insights ---
        # Most demanding area (by task volume)
        most_demanding_area = tasks.values('item__area').annotate(task_count=Count('id')).order_by('-task_count').first()
        
        context.update({
            'overdue_tasks_count': overdue_tasks_count,
            'tasks_due_this_week': tasks_due_this_week,
            'broken_items_count': broken_items_count,
            'total_active_items': total_active_items,
            'total_asset_value': total_asset_value,
            'warranty_watch': warranty_watch,
            'maintenance_load': maintenance_load,
            'next_up_tasks': next_up_tasks,
            'most_demanding_area': most_demanding_area,
        })

    return render(request, "home.html", context)