from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from common.views import serve_upload

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("common.urls")),
    path("", include("upkeep.urls")),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="/login/"), name="logout"),
    # Uploads are served by the app rather than the proxy so they can be scoped
    # to the account that owns them — receipts hold purchase records and would
    # otherwise be readable by anyone who knows or guesses the URL.
    # django.conf.urls.static is not used here because it silently no-ops when
    # DEBUG is False.
    path("media/<path:path>", serve_upload, name="media"),
]
