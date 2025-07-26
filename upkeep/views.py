from collections import defaultdict
from django.db.models import Count, Q, Prefetch
from django.utils import timezone
from .models import Task, Item, Location
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from .forms import ItemForm, LocationForm
from common.forms import ProfileForm
from common.models import Profile


@login_required
def settings_view(request):
    user = request.user

    # Get or create profile
    profile, _ = Profile.objects.get_or_create(user=user)

    # Handle profile update
    if request.method == "POST":
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        if profile_form.is_valid():
            profile_form.save()
            return redirect("settings-view")
    else:
        profile_form = ProfileForm(instance=profile)

    # Handle locations
    locations = Location.objects.filter(user=user).order_by("-default", "name")
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
        },
    )


@login_required
def location_delete(request, pk):
    location = get_object_or_404(Location, pk=pk, user=request.user)

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
def location_create(request):
    if request.method == "POST":
        form = LocationForm(request.POST)
        if form.is_valid():
            location = form.save(commit=False)
            location.user = request.user
            location.default = False  # just to be explicit
            location.save()
            messages.success(request, f"Location '{location.name}' created.")
            return redirect("settings-view")
    else:
        form = LocationForm()
    return render(request, "location_form.html", {"form": form})


@login_required
def location_update(request, pk):
    location = get_object_or_404(Location, pk=pk, user=request.user)

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
    item = get_object_or_404(Item, pk=pk, user=request.user)
    if request.method == "POST":
        item.status = Item.ItemStatus.RETIRED
        item.save()
        messages.success(request, f"{item.name} has been archived.")
    return redirect("item-list")


@login_required
def item_update(request, pk):
    item = get_object_or_404(Item, pk=pk, user=request.user)

    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f"{item.name} was updated successfully.")
            return redirect("item-list")  # or wherever the item list is shown
    else:
        form = ItemForm(instance=item)

    return render(
        request, "components/item_detail_modal.html", {"item": item, "form": form}
    )


@login_required
def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk, user=request.user)

    if request.method == "POST":
        item_name = item.name
        item.delete()
        messages.success(request, f"Item '{item_name}' was deleted successfully.")
        return redirect("item-list")


@login_required
def item_create(request):
    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            # All new items should have status ACTIVE
            item.status = Item.ItemStatus.ACTIVE
            item.user = request.user
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
        form = ItemForm()

    # Optional: this view can render a standalone page or return a partial if needed
    return render(request, "inventory/item_create.html", {"form": form})


@login_required
def item_list(request):
    items = (
        Item.objects.filter(user=request.user)
        .select_related("location")
        .order_by("location__name", "name")
    )

    # empty form for item create
    form = ItemForm()

    for item in items:
        item.form = ItemForm(instance=item)  # Attach form directly

    grouped_items = defaultdict(list)
    for item in items:
        loc_name = item.location.name if item.location else "No location"
        grouped_items[loc_name].append(item)

    context = {
        "grouped_items": grouped_items.items(),
        "form": form,
    }
    return render(request, "item_list.html", context)


@login_required
def maintenance_list(request):
    today = timezone.now().date()
    start_of_month = today.replace(day=1)

    task_queryset = Task.objects.all()

    item_queryset = (
        Item.objects.filter(user=request.user)
        .annotate(
            total_task_count=Count("tasks"),
            due_task_count=Count("tasks", filter=Q(tasks__next_due_date__lte=today)),
            tasks_completed_for_period=Count(
                "tasks",
                filter=Q(
                    tasks__last_performed__gte=start_of_month,
                    tasks__last_performed__lte=today,
                ),
            ),
        )
        .prefetch_related(Prefetch("tasks", queryset=task_queryset))
    )

    locations = (
        Location.objects.filter(user=request.user)
        .annotate(
            total_task_count=Count("items__tasks"),
            due_task_count=Count(
                "items__tasks", filter=Q(items__tasks__next_due_date__lte=today)
            ),
            tasks_completed_for_period=Count(
                "items__tasks",
                filter=Q(
                    items__tasks__last_performed__gte=start_of_month,
                    items__tasks__last_performed__lte=today,
                ),
            ),
        )
        .prefetch_related(Prefetch("items", queryset=item_queryset))
    )

    context = {
        "locations": locations,
        "title": "UPKEEP",
    }

    return render(request, "upkeep.html", context)
