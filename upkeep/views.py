from collections import defaultdict
from django.db.models import Q
from django.utils import timezone
from django.db.models.functions import Coalesce, Greatest
from .models import Task, Item, Location
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from .forms import ItemForm, LocationForm, TaskForm
from common.forms import ProfileForm
from common.models import Profile
import datetime


@login_required
def settings_view(request):
    user = request.user

    # Get or create profile
    profile, _ = Profile.objects.get_or_create(user=user)
    account = profile.account

    # Handle profile and account update
    if request.method == "POST":
        if "update_profile" in request.POST:
            profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated.")
                return redirect("settings-view")
        elif "update_household" in request.POST and account:
            household_name = request.POST.get("household_name")
            if household_name:
                account.name = household_name
                account.save()
                messages.success(request, f"Household renamed to {household_name}.")
                return redirect("settings-view")
        elif "create_household" in request.POST and not account:
            household_name = request.POST.get("household_name")
            if household_name:
                from common.models import Account
                new_account = Account.objects.create(name=household_name, owner=user)
                profile.account = new_account
                profile.save()
                messages.success(request, f"Household '{household_name}' created.")
                return redirect("settings-view")
        elif "add_member" in request.POST and account:
            username = request.POST.get("new_username")
            password = request.POST.get("new_password")
            email = request.POST.get("new_email", "")
            
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            if User.objects.filter(username=username).exists():
                messages.error(request, f"Username '{username}' already exists.")
            else:
                new_user = User.objects.create_user(username=username, email=email, password=password)
                new_profile = Profile.objects.create(user=new_user, account=account)
                messages.success(request, f"Member '{username}' added to the household.")
                return redirect("settings-view")
    
    profile_form = ProfileForm(instance=profile)

    # Handle locations
    locations = []
    members = []
    if account:
        locations = Location.objects.filter(account=account).order_by("-default", "name")
        members = account.members.select_related('user').all()
    
    for loc in locations:
        loc.form = LocationForm(instance=loc)
    form = LocationForm()

    return render(
        request,
        "settings.html",
        {
            "locations": locations,
            "form": form,
            "profile_form": profile_form,
            "account": account,
            "members": members,
        },
    )


@login_required
def location_delete(request, pk):
    location = get_object_or_404(Location, pk=pk, account=request.user.profile.account)

    if location.default:
        messages.error(request, "The default location cannot be deleted.")
        return redirect("settings-view")

    if request.method == "POST":
        location.delete()
        messages.success(
            request, f"Location '{location.name}' was deleted successfully."
        )
        return redirect("settings-view")


@login_required
def switch_location(request, pk):
    location = get_object_or_404(Location, pk=pk, account=request.user.profile.account)
    request.session["active_location_id"] = location.id
    messages.success(request, f"Switched to location: {location.name}")

    # Redirect to where the user came from, or default to home/item-list
    next_url = request.META.get("HTTP_REFERER", "item-list")
    return redirect(next_url)


@login_required
def location_create(request):
    if request.method == "POST":
        form = LocationForm(request.POST)
        if form.is_valid():
            location = form.save(commit=False)
            location.account = request.user.profile.account
            location.default = False  # just to be explicit
            location.save()
            messages.success(request, f"Location '{location.name}' created.")
            return redirect("settings-view")
    else:
        form = LocationForm()
    return render(request, "location_form.html", {"form": form})


@login_required
def location_update(request, pk):
    location = get_object_or_404(Location, pk=pk, account=request.user.profile.account)

    if request.method == "POST":
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, f"Location '{location.name}' updated.")
            return redirect("settings-view")
    else:
        form = LocationForm(instance=location)

    return render(request, "location_form.html", {"form": form})


@login_required
def item_archive(request, pk):
    item = get_object_or_404(Item, pk=pk, location__account=request.user.profile.account)
    if request.method == "POST":
        item.status = Item.ItemStatus.RETIRED
        item.save()
        messages.success(request, f"{item.name} has been archived.")
    return redirect("item-list")


@login_required
def item_update(request, pk):
    account = request.user.profile.account
    item = get_object_or_404(Item, pk=pk, location__account=account)

    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES, instance=item, account=account)
        if form.is_valid():
            form.save()
            messages.success(request, f"{item.name} was updated successfully.")
            return redirect("item-list")  # or wherever the item list is shown
    else:
        form = ItemForm(instance=item, account=account)

    return render(
        request, "components/item_detail_modal.html", {"item": item, "form": form}
    )


@login_required
def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk, location__account=request.user.profile.account)

    if request.method == "POST":
        item_name = item.name
        item.delete()
        messages.success(request, f"Item '{item_name}' was deleted successfully.")
        return redirect("item-list")


@login_required
def item_create(request):
    account = request.user.profile.account
    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES, account=account)
        if form.is_valid():
            item = form.save(commit=False)
            # All new items should have status ACTIVE
            item.status = Item.ItemStatus.ACTIVE
            item.save()
            messages.success(
                request,
                f"Item: {item.name} in location: {item.location.name} created successfully.",
            )
            return redirect("item-list")
        else:
            messages.error(
                request,
                "There was a problem creating the item. Please check the form for errors.",
            )
    else:
        initial_data = {}
        active_location_id = request.session.get("active_location_id")
        if active_location_id:
            initial_data["location"] = active_location_id
        form = ItemForm(initial=initial_data, account=account)

    # Optional: this view can render a standalone page or return a partial if needed
    return render(request, "inventory/item_create.html", {"form": form})


@login_required
def item_list(request):
    query = request.GET.get("q", "")
    account = request.user.profile.account

    items = Item.objects.filter(location__account=account).select_related("location")

    # Filter by active location
    active_location_id = request.session.get("active_location_id")
    if active_location_id:
        items = items.filter(location_id=active_location_id)
    else:
        # Fallback: pick default
        default_loc = (
            Location.objects.filter(account=account)
            .order_by("-default", "name")
            .first()
        )
        if default_loc:
            items = items.filter(location=default_loc)
            request.session["active_location_id"] = default_loc.id

    if query:
        items = items.filter(
            Q(name__icontains=query)
            | Q(brand__icontains=query)
            | Q(area__icontains=query)
        )

    items = items.order_by("area", "name")

    for item in items:
        item.form = ItemForm(instance=item, account=account)

    # No longer grouping by location.
    # We can group by Area if desired, or just pass flat list.
    # The template expects 'grouped_items', so let's adjust the template or adapter here.
    # Let's pass 'items' directly and update the template to iterate over items.

    context = {
        "items": items,
        "form": ItemForm(account=account),
    }

    if request.htmx:
        # Only return the list portion when HTMX requests it
        return render(request, "components/_item_list.html", context)

    return render(request, "item_list.html", context)


@login_required
def task_management_list(request):
    """
    Master list of all maintenance tasks, grouped by:
    - Item (Item -> Tasks) [default]
    - Frequency (Frequency -> Tasks)
    - Area (Item.area -> Tasks)
    """
    query = request.GET.get("q", "")
    group_by = request.GET.get("group_by", "item")
    account = request.user.profile.account

    # Base query: Get all tasks for the user
    tasks = Task.objects.filter(item__location__account=account).select_related(
        "item", "item__location"
    )

    # Filter by active location
    active_location_id = request.session.get("active_location_id")
    if active_location_id:
        tasks = tasks.filter(item__location_id=active_location_id)
    else:
        default_loc = (
            Location.objects.filter(account=account)
            .order_by("-default", "name")
            .first()
        )
        if default_loc:
            tasks = tasks.filter(item__location=default_loc)
            request.session["active_location_id"] = default_loc.id

    if query:
        tasks = tasks.filter(
            Q(name__icontains=query)
            | Q(item__name__icontains=query)
            | Q(description__icontains=query)
        )

    context = {
        "grouping_type": group_by,
        "form": TaskForm(account=account),
    }

    if group_by == "area":
        # Group by Area
        # structure: { "AreaName": [Task, Task] }
        tasks = tasks.order_by("item__area", "item__name", "name")
        grouped_tasks = defaultdict(list)
        for task in tasks:
            label = task.item.area if task.item.area else "General"
            grouped_tasks[label].append(task)
        context["grouped_tasks"] = dict(grouped_tasks)

    elif group_by == "frequency":
        # Group by frequency
        # structure: { "FrequencyLabel": [Task, Task] }
        tasks = tasks.order_by("frequency", "name")
        grouped_tasks = defaultdict(list)
        for task in tasks:
            label = task.get_frequency_display()
            grouped_tasks[label].append(task)
        context["grouped_tasks"] = dict(grouped_tasks)

    else:  # group_by == "item" (default)
        # Grouping logic: Item -> Tasks (No longer Location -> Item -> Tasks)
        # structure: { "ItemName": [Task, Task] }
        tasks = tasks.order_by("item__name", "name")
        grouped_tasks = defaultdict(list)

        for task in tasks:
            item_name = task.item.name
            grouped_tasks[item_name].append(task)

        context["grouped_tasks"] = dict(grouped_tasks)

    if request.htmx:
        # If it's an HTMX request, we can still return the full template
        # and let HTMX use hx-select if specified, or just return the full thing
        # and HTMX will swap the whole #task-list-container content.
        # However, to avoid returning the whole base.html wrapper, we can check for HTMX.
        pass

    return render(request, "maintenance_list.html", context)


@login_required
def task_create(request):
    """
    Creates a new task. Can be triggered from Maintenance page or Item Details.
    """
    account = request.user.profile.account
    if request.method == "POST":
        form = TaskForm(request.POST, account=account)
        if form.is_valid():
            task = form.save(commit=False)
            # Verify the item belongs to the account
            if task.item.location.account != account:
                messages.error(request, "You cannot add tasks to items you don't own.")
                return redirect("task-management-list")

            task.save()
            messages.success(
                request, f"Task '{task.name}' created for '{task.item.name}'."
            )

            # Redirect based on where the user came from?
            # For now, default to maintenance list.
            return redirect("task-management-list")
        else:
            # If HTMX, we should return the form with errors
            pass
    else:
        initial_data = {}
        item_id = request.GET.get("item")
        if item_id:
            item = get_object_or_404(Item, pk=item_id, location__account=account)
            initial_data["item"] = item

        form = TaskForm(initial=initial_data, account=account)
        # Filter the 'item' dropdown to only show Account's items in active location
        items_qs = Item.objects.filter(location__account=account)
        active_location_id = request.session.get("active_location_id")
        if active_location_id:
            items_qs = items_qs.filter(location_id=active_location_id)
        form.fields["item"].queryset = items_qs

    return render(request, "components/_task_create_modal.html", {"form": form})


@login_required
def task_update(request, pk):
    account = request.user.profile.account
    task = get_object_or_404(Task, pk=pk, item__location__account=account)

    if request.method == "POST":
        form = TaskForm(request.POST, instance=task, account=account)
        if form.is_valid():
            # Check if item changed and is valid
            updated_task = form.save(commit=False)
            if updated_task.item.location.account != account:
                messages.error(request, "Invalid item selection.")
                return redirect("task-management-list")

            updated_task.save()
            messages.success(request, f"Task '{task.name}' updated.")
            return redirect("task-management-list")
    else:
        form = TaskForm(instance=task, account=account)
        items_qs = Item.objects.filter(location__account=account)
        active_location_id = request.session.get("active_location_id")
        if active_location_id:
            items_qs = items_qs.filter(location_id=active_location_id)
        form.fields["item"].queryset = items_qs

    return render(
        request, "components/_task_create_modal.html", {"form": form, "task": task}
    )


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, item__location__account=request.user.profile.account)

    if request.method == "POST":
        task_name = task.name
        task.delete()
        messages.success(request, f"Task '{task_name}' deleted.")
        return redirect("task-management-list")

    # Optional: Confirmation modal logic if GET
    return render(request, "components/_task_delete_confirm_modal.html", {"task": task})


@login_required
def task_complete(request, pk):
    task = get_object_or_404(Task, pk=pk, item__location__account=request.user.profile.account)
    if request.method == "POST":
        task.last_performed = timezone.now().date()
        # Force recalculation of next due date
        task.next_due_date = task.calculate_next_due_date()
        # Reset snooze data
        task.snooze_count = 0
        task.snoozed_until = None
        task.save()
        messages.success(request, f"Task '{task.name}' marked as completed.")

        if request.htmx:
            from django.http import HttpResponse

            return HttpResponse("")

        # Redirect to where the user came from
        next_url = request.META.get("HTTP_REFERER", "task-due-list")
        return redirect(next_url)

    # If GET, technically we shouldn't do anything or show a confirmation?
    # For now, redirect to list.
    return redirect("task-due-list")


@login_required
def task_snooze(request, pk):
    task = get_object_or_404(Task, pk=pk, item__location__account=request.user.profile.account)
    if request.method == "POST":
        # Snooze for exactly 7 days from today
        task.snoozed_until = timezone.now().date() + datetime.timedelta(days=7)
        task.snooze_count += 1
        task.save()
        messages.success(
            request,
            f"Task '{task.name}' snoozed for 1 week from today. (Total snoozes: {task.snooze_count})",
        )
    return redirect("task-due-list")


@login_required
def task_due_list(request):
    """
    Shows only tasks that are due today or overdue, considering snoozes.
    Sorted from least overdue (closest to today) to most overdue.
    """

    today = timezone.now().date()
    account = request.user.profile.account

    # Task is due if:

    # 1. It is snoozed and the snooze has expired: snoozed_until <= today

    # 2. It is NOT snoozed and it is due: snoozed_until IS NULL AND next_due_date <= today

    tasks = (
        Task.objects.filter(item__location__account=account)
        .filter(
            Q(snoozed_until__lte=today)
            | Q(snoozed_until__isnull=True, next_due_date__lte=today)
        )
        .annotate(
            # Calculate the effective due date for sorting.
            # We use the later of next_due_date and snoozed_until.
            effective_due_date=Greatest(
                Coalesce("next_due_date", "snoozed_until"),
                Coalesce("snoozed_until", "next_due_date"),
            )
        )
        .select_related("item", "item__location")
        .order_by("-effective_due_date", "name")
    )

    # Filter by active location

    active_location_id = request.session.get("active_location_id")

    if active_location_id:
        tasks = tasks.filter(item__location_id=active_location_id)

    else:
        # Standard fallback if needed, or show all?

        # Existing pattern uses default location if none selected.

        default_loc = (
            Location.objects.filter(account=account)
            .order_by("-default", "name")
            .first()
        )

        if default_loc:
            tasks = tasks.filter(item__location=default_loc)

            request.session["active_location_id"] = default_loc.id

    context = {"tasks": tasks, "today": today}

    return render(request, "task_due_list.html", context)

    context = {"tasks": tasks, "today": today}

    return render(request, "task_due_list.html", context)
