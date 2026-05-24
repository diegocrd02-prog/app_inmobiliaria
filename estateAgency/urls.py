from django.urls import path

from . import views
from .views import PropertiesView, PropertyDetailView, ComparePropertiesView
app_name = "estateAgency"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("properties/", PropertiesView.as_view(), name="properties"),
    path("properties/compare/", ComparePropertiesView.as_view(), name="compare_properties"),
    path("properties/<int:pk>/", PropertyDetailView.as_view(), name="property_detail"),
    path("scraping/status/", views.scraping_status, name="scraping_status"),
]
