from django.contrib import admin
from .models import Equipment, MaintenanceLog, Multimedia, Message, Notification

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'equipment_type', 'location', 'created_by', 'created_at']
    list_filter = ['equipment_type', 'location']
    search_fields = ['name', 'manufacturer', 'model_number']

@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'activity_type', 'date_performed', 'performed_by', 'time_taken_minutes']
    list_filter = ['activity_type', 'date_performed']
    search_fields = ['description', 'parts_replaced']

@admin.register(Multimedia)
class MultimediaAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'media_type', 'uploaded_by', 'uploaded_at']
    list_filter = ['media_type']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'subject', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['subject', 'body']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']