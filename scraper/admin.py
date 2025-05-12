from django.contrib import admin

from scraper.models import *

# Register your models here.
admin.site.register(ScrapedData)
admin.site.register(Tenant)
admin.site.register(Product)
admin.site.register(Competitor)
admin.site.register(CompetitorProduct)
