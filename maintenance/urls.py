from django.urls import path
from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),

    path('equipment/', views.EquipmentListView.as_view(), name='equipment_list'),
    path('equipment/create/', views.EquipmentCreateView.as_view(), name='equipment_create'),
    path('equipment/<int:pk>/', views.EquipmentDetailView.as_view(), name='equipment_detail'),
    path('equipment/<int:pk>/update/', views.EquipmentUpdateView.as_view(), name='equipment_update'),
    path('equipment/<int:pk>/delete/', views.EquipmentDeleteView.as_view(), name='equipment_delete'),

    path('logs/', views.MaintenanceLogListView.as_view(), name='maintenance_log_list'),
    path('logs/create/', views.MaintenanceLogCreateView.as_view(), name='maintenance_log_create'),
    path('logs/<int:pk>/', views.MaintenanceLogDetailView.as_view(), name='maintenance_log_detail'),

    path('upload/', views.MultimediaUploadView.as_view(), name='multimedia_upload'),

    path('messages/', views.MessageListView.as_view(), name='message_list'),
    path('messages/create/', views.MessageCreateView.as_view(), name='message_create'),
    path('messages/<int:pk>/', views.MessageDetailView.as_view(), name='message_detail'),
    path('messages/<int:pk>/reply/', views.ReplyMessageView.as_view(), name='message_reply'),

    path('notifications/', views.NotificationListView.as_view(), name='notification_list'),
    path('notifications/<int:pk>/read/', views.MarkNotificationReadView.as_view(), name='notification_read'),
    path('notifications/read/all/', views.MarkAllNotificationsReadView.as_view(), name='notifications_read_all'),
    path('record/', views.RecordMediaView.as_view(), name='record_media'),
path('recordings/upload/', views.UploadRecordingView.as_view(), name='upload_recording'),
]