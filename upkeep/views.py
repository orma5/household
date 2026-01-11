from collections import defaultdict
from django.db.models import Count, Q, Prefetch
from django.utils import timezone
from .models import Task, Item, Location
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from .forms import ItemForm, LocationForm, TaskForm
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
    query = request.GET.get("q", "")

    items = Item.objects.filter(user=request.user).select_related("location")

    if query:
        items = items.filter(
            Q(name__icontains=query)
            | Q(brand__icontains=query)
            | Q(area__icontains=query)
        )

    items = items.order_by("location__name", "name")

    for item in items:
        item.form = ItemForm(instance=item)

    grouped_items = defaultdict(list)
    for item in items:
        loc_name = item.location.name if item.location else "No location"
        grouped_items[loc_name].append(item)

    context = {
        "grouped_items": grouped_items.items(),
        "form": ItemForm(),
    }

    if request.htmx:
        # Only return the list portion when HTMX requests it
        return render(request, "components/_item_list.html", context)

    return render(request, "item_list.html", context)

@login_required
def task_management_list(request):
    """
    Master list of all maintenance tasks, grouped by:
    - Item (Location -> Item) [default]
    - Frequency (Frequency -> Tasks)
    - None (Flat list)
    """
    query = request.GET.get("q", "")
    group_by = request.GET.get("group_by", "item")

    # Base query: Get all tasks for the user
    tasks = Task.objects.filter(item__user=request.user).select_related(
        "item", "item__location"
    )

    if query:
        tasks = tasks.filter(
            Q(name__icontains=query)
            | Q(item__name__icontains=query)
            | Q(description__icontains=query)
        )

    context = {
        "grouping_type": group_by,
        "form": TaskForm(),
    }

    if group_by == "none":
        # Flat list
        tasks = tasks.order_by("name")
        context["tasks"] = tasks

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
        # Grouping logic: Location -> Item -> Tasks
        # structure: { "LocationName": { "ItemName": [Task, Task] } }
        tasks = tasks.order_by("item__location__name", "item__name", "name")
        grouped_tasks = defaultdict(lambda: defaultdict(list))

        for task in tasks:
            loc_name = task.item.location.name if task.item.location else "Unassigned"
            item_name = task.item.name
            grouped_tasks[loc_name][item_name].append(task)

        # Convert to standard dict for safety
        final_grouped_tasks = {
            loc: dict(items) for loc, items in grouped_tasks.items()
        }
        context["grouped_tasks"] = final_grouped_tasks

    if request.htmx and query:
        # Note: HTMX filtering logic might need to be specific if we want partials.
        # For now, we return the full page which HTMX will parse and swap.
        pass

    return render(request, "maintenance_list.html", context)


@login_required
def task_create(request):
    """
    Creates a new task. Can be triggered from Maintenance page or Item Details.
    """
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            # Verify the item belongs to the user
            if task.item.user != request.user:
                 messages.error(request, "You cannot add tasks to items you don't own.")
                 return redirect("task-management-list")
            
            task.save()
            messages.success(request, f"Task '{task.name}' created for '{task.item.name}'.")
            
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
            item = get_object_or_404(Item, pk=item_id, user=request.user)
            initial_data["item"] = item
            
        form = TaskForm(initial=initial_data)
        # Filter the 'item' dropdown to only show User's items
        form.fields["item"].queryset = Item.objects.filter(user=request.user)

    return render(request, "components/_task_create_modal.html", {"form": form})


@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk, item__user=request.user)

    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            # Check if item changed and is valid
            updated_task = form.save(commit=False)
            if updated_task.item.user != request.user:
                messages.error(request, "Invalid item selection.")
                return redirect("task-management-list")
            
            updated_task.save()
            messages.success(request, f"Task '{task.name}' updated.")
            return redirect("task-management-list")
    else:
        form = TaskForm(instance=task)
        form.fields["item"].queryset = Item.objects.filter(user=request.user)

    return render(request, "components/_task_create_modal.html", {"form": form, "task": task})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, item__user=request.user)

    if request.method == "POST":
        task_name = task.name
        task.delete()
        messages.success(request, f"Task '{task_name}' deleted.")
        return redirect("task-management-list")
    
    # Optional: Confirmation modal logic if GET
    return render(request, "components/_task_delete_confirm_modal.html", {"task": task})
