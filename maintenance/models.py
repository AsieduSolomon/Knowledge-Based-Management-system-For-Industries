from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Equipment(models.Model):
    EQUIPMENT_TYPES = [
        ('boiler', 'Steam Boiler'),
        ('motor', 'Electric Motor'),
        ('conveyor', 'Conveyor System'),
        ('mixer', 'Industrial Mixer'),
        ('packaging', 'Packaging Machine'),
        ('panel', 'Control Panel'),
        ('other', 'Other Equipment'),
    ]

    name = models.CharField(max_length=200)
    equipment_type = models.CharField(max_length=50, choices=EQUIPMENT_TYPES)
    location = models.CharField(max_length=200)
    manufacturer = models.CharField(max_length=200, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    installation_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='equipment_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.get_equipment_type_display()}"

    def get_recent_logs(self):
        return self.maintenance_logs.order_by('-date_performed')[:5]

    def get_documentation_completeness(self):
        completeness = 0
        if self.manufacturer:
            completeness += 20
        if self.model_number:
            completeness += 20
        if self.installation_date:
            completeness += 20
        if self.maintenance_logs.count() > 0:
            completeness += 20
        if self.multimedia_files.count() > 0:
            completeness += 20
        return completeness

class MaintenanceLog(models.Model):
    ACTIVITY_TYPES = [
        ('preventive', 'Preventive Maintenance'),
        ('corrective', 'Corrective Maintenance'),
        ('inspection', 'Inspection'),
        ('emergency', 'Emergency Repair'),
    ]

    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='maintenance_logs')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    date_performed = models.DateTimeField(default=timezone.now)
    description = models.TextField()
    parts_replaced = models.TextField(blank=True)
    time_taken_minutes = models.PositiveIntegerField()
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='maintenance_logs')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.equipment.name} - {self.get_activity_type_display()} - {self.date_performed.date()}"



class Multimedia(models.Model):
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('diagram', 'Wiring Diagram'),
        ('audio', 'Audio Recording'),
        ('video', 'Video Recording'),
        ('document', 'Document'),
    ]

    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='multimedia_files')
    maintenance_log = models.ForeignKey(MaintenanceLog, on_delete=models.CASCADE, null=True, blank=True, related_name='multimedia_files')
    media_type = models.CharField(max_length=50, choices=MEDIA_TYPES)
    file = models.FileField(upload_to='equipment_media/%Y/%m/%d/')
    description = models.CharField(max_length=500, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='multimedia_uploads')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.equipment.name} - {self.get_media_type_display()}"

    def filename(self):
        return self.file.name.split('/')[-1]

    def file_extension(self):
        name = self.file.name.lower()
        if name.endswith('.mp3'):
            return 'mp3'
        elif name.endswith('.wav'):
            return 'wav'
        elif name.endswith('.m4a'):
            return 'm4a'
        elif name.endswith('.mp4'):
            return 'mp4'
        elif name.endswith('.webm'):
            return 'webm'
        elif name.endswith('.mov'):
            return 'mov'
        elif name.endswith('.jpg') or name.endswith('.jpeg'):
            return 'jpg'
        elif name.endswith('.png'):
            return 'png'
        elif name.endswith('.pdf'):
            return 'pdf'
        else:
            return 'unknown'

    def is_audio(self):
        return self.media_type == 'audio'

    def is_video(self):
        return self.media_type == 'video'

    def is_image(self):
        return self.media_type in ['image', 'diagram']




class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    parent_message = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    def __str__(self):
        return f"From {self.sender.username} to {self.recipient.username}: {self.subject[:50]}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('maintenance_due', 'Maintenance Due'),
        ('message_received', 'New Message'),
        ('log_created', 'Maintenance Log Created'),
        ('equipment_added', 'New Equipment Added'),
        ('reminder', 'Documentation Reminder'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title[:50]}"

    class Meta:
        ordering = ['-created_at']