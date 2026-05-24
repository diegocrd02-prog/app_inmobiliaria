from django.contrib import admin
from .models import Property
from .models import Source
from .models import Location
from .models import Property
from .models import Listing
from .models import Prediction
from .models import AreaStats
from .models import ScrapingLog

admin.site.register(Property)
admin.site.register(Source)
admin.site.register(Location)
admin.site.register(Listing)
admin.site.register(Prediction)
admin.site.register(AreaStats)
admin.site.register(ScrapingLog)

# Register your models here.
