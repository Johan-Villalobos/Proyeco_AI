from django.urls import path

from simulator import views


urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("api/scenarios/", views.scenarios_api, name="scenarios_api"),
    path("api/simulate/", views.simulate_api, name="simulate_api"),
    path("api/validate/", views.validate_api, name="validate_api"),
    path("api/history/", views.history_api, name="history_api"),
]
