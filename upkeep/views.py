from django.db.models import Count, Q, Prefetch
from datetime import date
from django.shortcuts import render
from django.utils import timezone
from .models import Task, Item, Location


from datetime import date
from django.db.models import Count, Q, Prefetch
from django.utils import timezone

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
            "name": "Tracked Items",
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

    item_queryset = (
        Item.objects
        .annotate(
            total_task_count=Count('tasks'),
            due_task_count=Count('tasks', filter=Q(tasks__next_due_date__lte=today)),
            tasks_completed_for_period=Count(
                'tasks',
                filter=Q(tasks__last_performed__gte=start_of_month, tasks__last_performed__lte=today)
            ),
        )
        .prefetch_related(Prefetch('tasks', queryset=task_queryset))
    )

    locations = (
        Location.objects
        .annotate(
            total_task_count=Count('items__tasks'),
            due_task_count=Count('items__tasks', filter=Q(items__tasks__next_due_date__lte=today)),
            tasks_completed_for_period=Count(
                'items__tasks',
                filter=Q(items__tasks__last_performed__gte=start_of_month, items__tasks__last_performed__lte=today)
            ),
        )
        .filter(items__isnull=False)
        .prefetch_related(Prefetch('items', queryset=item_queryset))
    )

    context = {
        "kpis": kpis,
        "locations": locations,
        "title": "UPKEEP",
    }

    return render(request, "upkeep.html", context)

