from django.contrib import admin

# Register your models here.
from .models import Petition


class PetitionAdmin(admin.ModelAdmin):
    list_display = [
		"entity",
		"status_data",
		"status_petition",
		"folio_petition",
		"folio_complain",
    ]
    list_filter = ["entity"]

admin.site.register(Petition, PetitionAdmin)

