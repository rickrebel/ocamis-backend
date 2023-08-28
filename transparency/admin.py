from django.contrib import admin
from django.utils.html import format_html

from .models import Anomaly, TransparencyIndex, TransparencyLevel


# Register your models here.
class AnomalyAdmin(admin.ModelAdmin):
    list_display = ["public_name", "name", "is_public", "description"]


class TransparencyLevelInline(admin.StackedInline):
    model = TransparencyLevel
    extra = 0


class TransparencyIndexAdmin(admin.ModelAdmin):
    list_display = ["short_name", "public_name", "description"]
    inlines = [ TransparencyLevelInline ]


class TransparencyLevelAdmin(admin.ModelAdmin):
    list_display = [
        "short_name", "public_name", "display_index", "display_final", "value",
        "order_viz", "value_ctrls", "value_pets", "is_default"]
    list_editable = [
        "value", "order_viz", "value_ctrls", "value_pets", "is_default"]
    list_filter = ["transparency_index"]

    def display_index(self, obj):
        names = [
            obj.transparency_index.public_name,
            f"({obj.transparency_index.short_name})"]
        return format_html("<br>".join(names))
    display_index.short_description = "Indicador"

    def display_final(self, obj):
        return format_html(obj.final_level.public_name) if obj.final_level else ""
    display_final.short_description = "Concentrado destino"


admin.site.register(Anomaly, AnomalyAdmin)
admin.site.register(TransparencyIndex, TransparencyIndexAdmin)
admin.site.register(TransparencyLevel, TransparencyLevelAdmin)
