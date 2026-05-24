from django.shortcuts import get_object_or_404, render
from django.views import generic
from .services import propertyService, locationService, chartService, comparisonService
from django.http import JsonResponse
from django.core.cache import cache
from .models import Property
import json
import re

PROPERTY_IMAGE_PATTERN = re.compile(r"^estateAgency/img/(flat|house|unknown)-\d{2}\.jpg$")

class IndexView(generic.TemplateView):
    template_name = "estateAgency/index.html"
    def get_context_data(self, **kwargs):
        isPropertyDatabaseEmpty = not Property.objects.exists()
        context = super().get_context_data(**kwargs)

        locations = locationService.get_all_locations()
        context["locations"] = locations
        context["isPropertyDatabaseEmpty"] = isPropertyDatabaseEmpty

        return context
    
class PropertiesView(generic.TemplateView):

    template_name = "estateAgency/properties.html"

    def get_context_data(self, **kwargs):
        isPropertyDatabaseEmpty = not Property.objects.exists()
        context = super().get_context_data(**kwargs)

        flag = self.request.GET.get("type")
        city = self.request.GET.get("city")


        if flag not in ["sale", "rent_short", "rent_long"]:
            flag = "sale"

        properties = propertyService.get_properties_by_operation(flag, city=city)
        chart_data = chartService.get_chart_data_by_operation(flag, city=city)
        market_summary = chartService.get_market_summary(flag, city=city)

        context["properties"] = properties
        context["selected_type"] = flag
        context["selected_city"] = city
        context["chart_data"] = json.dumps(chart_data)
        context["market_summary"] = market_summary
        context["locations"] = locationService.get_all_locations()
        context["isPropertyDatabaseEmpty"] = isPropertyDatabaseEmpty

        return context

class PropertyDetailView(generic.TemplateView):

    template_name = "estateAgency/property_detail.html"

    def get_context_data(self, **kwargs):
        isPropertyDatabaseEmpty = not Property.objects.exists()
        context = super().get_context_data(**kwargs)

        property_obj = get_object_or_404(
            Property.objects.select_related("location", "source").prefetch_related("listings"),
            pk=kwargs["pk"],
        )
        latest_listing = property_obj.listings.order_by("-scraped_at").first()
        chart_data = chartService.get_property_detail_chart_data(property_obj)

        if property_obj.operation_type == "sale":
            selected_type = "sale"
            operation_label = "Compra"
        elif property_obj.rental_type == "short":
            selected_type = "rent_short"
            operation_label = "Alquiler de temporada"
        else:
            selected_type = "rent_long"
            operation_label = "Alquiler de larga estancia"

        context["property"] = property_obj
        context["latest_listing"] = latest_listing
        context["chart_data"] = json.dumps(chart_data)
        context["selected_type"] = selected_type
        context["operation_label"] = operation_label
        context["isPropertyDatabaseEmpty"] = isPropertyDatabaseEmpty
        return context

class ComparePropertiesView(generic.TemplateView):

    template_name = "estateAgency/compare.html"

    def get_context_data(self, **kwargs):
        isPropertyDatabaseEmpty = not Property.objects.exists()
        context = super().get_context_data(**kwargs)

        selected_ids = self.request.GET.getlist("selected_ids")
        if not selected_ids:
            ids_param = self.request.GET.get("ids", "")
            selected_ids = [value.strip() for value in ids_param.split(",") if value.strip()]

        comparison = comparisonService.compare_properties(selected_ids)

        context["items"] = comparison["items"]
        context["best"] = comparison["best"]
        context["conclusion"] = comparison["conclusion"]
        context["isPropertyDatabaseEmpty"] = isPropertyDatabaseEmpty

        return context

def scraping_status(request):
    return JsonResponse({
        "running": bool(cache.get("pisos_scraping_running"))
    })
