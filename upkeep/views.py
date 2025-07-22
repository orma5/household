from collections import defaultdict
from django.db.models import Count, Q, Prefetch
from django.utils import timezone
from .models import Task, Item, Location
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from .forms import ItemForm


@login_required
def item_update(request, pk):
    item = get_object_or_404(Item, pk=pk)

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
    item = get_object_or_404(Item, pk=pk)

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
    items = Item.objects.select_related("location").order_by("location__name", "name")

    for item in items:
        item.form = ItemForm(instance=item)  # Attach form directly

    grouped_items = defaultdict(list)
    for item in items:
        loc_name = item.location.name if item.location else "No location"
        grouped_items[loc_name].append(item)

    context = {
        "grouped_items": grouped_items.items(),
    }
    return render(request, "item_list.html", context)


@login_required
def maintenance_list(request):
    today = timezone.now().date()
    start_of_month = today.replace(day=1)

    task_queryset = Task.objects.all()

    item_queryset = Item.objects.annotate(
        total_task_count=Count("tasks"),
        due_task_count=Count("tasks", filter=Q(tasks__next_due_date__lte=today)),
        tasks_completed_for_period=Count(
            "tasks",
            filter=Q(
                tasks__last_performed__gte=start_of_month,
                tasks__last_performed__lte=today,
            ),
        ),
    ).prefetch_related(Prefetch("tasks", queryset=task_queryset))

    locations = Location.objects.annotate(
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
    ).prefetch_related(Prefetch("items", queryset=item_queryset))

    context = {
        "locations": locations,
        "title": "UPKEEP",
    }

    return render(request, "upkeep.html", context)
