from django.db.models import Count, Q, Prefetch
from django.utils import timezone
from .models import Task, Item, Location
from django.shortcuts import render


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
