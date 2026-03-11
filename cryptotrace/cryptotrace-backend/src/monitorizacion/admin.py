import csv
from django.contrib import admin
from django.http import HttpResponse
from .models import UserAccessLog


@admin.register(UserAccessLog)
class UserAccessLogAdmin(admin.ModelAdmin):
    list_display = [
        "created_at",
        "user_email",
        "method",
        "path",
        "status_code",
        "ip_address",
        "response_time_ms",
    ]
    list_filter = ["method", "status_code", "created_at"]
    search_fields = ["path", "user__email", "ip_address"]
    raw_id_fields = ["user"]
    readonly_fields = [
        "user",
        "path",
        "method",
        "status_code",
        "ip_address",
        "user_agent",
        "response_time_ms",
        "created_at",
    ]
    date_hierarchy = "created_at"
    actions = ["export_to_csv"]

    def user_email(self, obj):
        return obj.user.email if obj.user_id else ""

    user_email.short_description = "Usuario"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.action(description="Exportar a CSV")
    def export_to_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=registro_acceso.csv"
        response.write("\ufeff")
        writer = csv.writer(response, dialect="excel")
        headers = [
            "Fecha",
            "Usuario",
            "Método",
            "Ruta",
            "Código",
            "IP",
            "User-Agent",
            "Tiempo (ms)",
        ]
        writer.writerow(headers)
        for obj in queryset.order_by("created_at"):
            user_email = obj.user.email if obj.user_id else ""
            writer.writerow([
                obj.created_at.isoformat() if obj.created_at else "",
                user_email,
                obj.method or "",
                obj.path or "",
                obj.status_code or "",
                str(obj.ip_address) if obj.ip_address else "",
                obj.user_agent or "",
                obj.response_time_ms or "",
            ])
        return response
