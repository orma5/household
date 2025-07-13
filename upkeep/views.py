from django.db.models import Count, Q, Prefetch
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from datetime import date
from django.utils import timezone
from .models import Task, Item, Location
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from .forms import TaskForm, ItemForm


from datetime import date
from django.db.models import Count, Q, Prefetch
from django.utils import timezone


class ItemListView(ListView):
    model = Item
    template_name = "items/item_list.html"
    context_object_name = "items"


class ItemCreateView(CreateView):
    model = Item
    fields = ["name", "purchase_year", "location", "sub_location", "initial_value"]
    template_name = "items/item_form.html"
    success_url = reverse_lazy("item-list")


class ItemUpdateView(UpdateView):
    model = Item
    fields = ["name", "purchase_year", "location", "sub_location", "initial_value"]
    template_name = "items/item_form.html"
    success_url = reverse_lazy("item-list")


class ItemDeleteView(DeleteView):
    model = Item
    template_name = "items/item_confirm_delete.html"
    success_url = reverse_lazy("item-list")


class LocationListView(ListView):
    model = Location
    template_name = "locations/location_list.html"
    context_object_name = "locations"


class LocationCreateView(CreateView):
    model = Location
    fields = ["name", "address", "zip_code", "city", "country_code"]
    template_name = "locations/location_form.html"
    success_url = reverse_lazy("location-list")


class LocationUpdateView(UpdateView):
    model = Location
    fields = ["name", "address", "zip_code", "city", "country_code"]
    template_name = "locations/location_form.html"
    success_url = reverse_lazy("location-list")


class LocationDeleteView(DeleteView):
    model = Location
    template_name = "locations/location_confirm_delete.html"
    success_url = reverse_lazy("location-list")


def upkeep_view(request):
    today = timezone.now().date()
    start_of_month = today.replace(day=1)

    # KPI 1: Tasks due today or overdue
    tasks_due_count = Task.objects.filter(next_due_date__lte=today).count()

    # KPI 2: Count of items
    items_count = Item.objects.count()

    # KPI 3: % completed this month
    tasks_completed_this_month = Task.objects.filter(
        last_performed__gte=start_of_month, last_performed__lte=today
    ).count()
    tasks_due_this_month = Task.objects.filter(
        next_due_date__gte=start_of_month, next_due_date__lte=today
    ).count()

    if tasks_completed_this_month + tasks_due_this_month > 0:
        completed_percentage = round(
            tasks_completed_this_month
            / (tasks_completed_this_month + tasks_due_this_month)
            * 100,
            2,
        )
    else:
        completed_percentage = 0

    kpis = [
        {
            "name": "Tasks Due",
            "value": tasks_due_count,
            "icon": "bi bi-stopwatch",
            "background_color": "#fcf6bd",
            "trend_icon": "",
        },
        {
            "name": "Tracked Inventory",
            "value": items_count,
            "icon": "bi bi-boxes",
            "background_color": "#d0f4de",
            "trend_icon": "",
        },
        {
            "name": "Completed (%)",
            "value": f"{completed_percentage}%",
            "icon": "bi bi-check2-circle",
            "background_color": "#a9def9",
            "trend_icon": "",
        },
    ]

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
        "kpis": kpis,
        "locations": locations,
        "title": "UPKEEP",
    }

    return render(request, "upkeep.html", context)


@require_POST
def create_task(request):
    """
    Handle creation of a new Task, and create an Item on-the-fly if needed.
    The modal sends:
      - name, description, frequency
      - location (id)
      - either item (id) OR new_item_name
    """
    task_form = TaskForm(request.POST)
    new_item_name = request.POST.get("new_item_name")
    location_id = request.POST.get("location")
    item_id = request.POST.get("item")
    # If user entered a new item name, create it
    if new_item_name:
        item = Item.objects.create(name=new_item_name, location_id=location_id)
        # Bind that new item into the task data
        data = request.POST.copy()
        data["item"] = item.pk
        task_form = TaskForm(data)
    if task_form.is_valid():
        task_form.save()
        return redirect(reverse("upkeep-list"))
    else:
        # On error, re‐render the upkeep page with form errors
        # You could instead return JSON for AJAX
        from .views import upkeep_view

        context = upkeep_view(request).context_data
        context.update({"task_form": task_form})
        return render(request, "upkeep.html", context)
