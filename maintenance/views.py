from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth import login
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Equipment, MaintenanceLog, Multimedia, Message, Notification
from .forms import EquipmentForm, MaintenanceLogForm, MultimediaForm, MessageForm, ReplyMessageForm, UserRegistrationForm
from django.views import View
from django.http import JsonResponse

class CustomLoginView(LoginView):
    template_name = 'maintenance/login.html'
    redirect_authenticated_user = True

class CustomLogoutView(LogoutView):
    next_page = 'login'

class RegisterView(CreateView):
    template_name = 'maintenance/register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Registration successful. Please log in.')
        return response

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'maintenance/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context['equipment_count'] = Equipment.objects.count()
        context['recent_logs'] = MaintenanceLog.objects.order_by('-date_performed')[:10]
        context['unread_notifications'] = Notification.objects.filter(user=user, is_read=False).count()
        context['unread_messages'] = Message.objects.filter(recipient=user, is_read=False).count()

        equipment_with_low_doc = []
        for eq in Equipment.objects.all():
            if eq.get_documentation_completeness() < 50:
                equipment_with_low_doc.append(eq)
        context['low_documentation_equipment'] = equipment_with_low_doc[:5]

        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        context['logs_last_30_days'] = MaintenanceLog.objects.filter(date_performed__gte=thirty_days_ago).count()

        return context

class EquipmentListView(LoginRequiredMixin, ListView):
    model = Equipment
    template_name = 'maintenance/equipment_list.html'
    context_object_name = 'equipment_list'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search', '')
        equipment_type = self.request.GET.get('type', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(location__icontains=search) |
                Q(manufacturer__icontains=search)
            )
        if equipment_type:
            queryset = queryset.filter(equipment_type=equipment_type)
        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['equipment_types'] = Equipment.EQUIPMENT_TYPES
        context['current_type'] = self.request.GET.get('type', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context

class EquipmentDetailView(LoginRequiredMixin, DetailView):
    model = Equipment
    template_name = 'maintenance/equipment_detail.html'
    context_object_name = 'equipment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['logs'] = self.object.maintenance_logs.order_by('-date_performed')[:20]
        context['multimedia'] = self.object.multimedia_files.all()
        context['documentation_completeness'] = self.object.get_documentation_completeness()
        return context

class EquipmentCreateView(LoginRequiredMixin, CreateView):
    model = Equipment
    form_class = EquipmentForm
    template_name = 'maintenance/equipment_form.html'
    success_url = reverse_lazy('equipment_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{self.request.user.id}',
            {
                'type': 'send_notification',
                'notification': {
                    'title': 'Equipment Added',
                    'message': f'New equipment "{form.instance.name}" has been added.',
                    'link': f'/equipment/{form.instance.id}/'
                }
            }
        )

        Notification.objects.create(
            user=self.request.user,
            notification_type='equipment_added',
            title='Equipment Added',
            message=f'You added new equipment: {form.instance.name}',
            link=f'/equipment/{form.instance.id}/'
        )

        messages.success(self.request, 'Equipment created successfully.')
        return response

class EquipmentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Equipment
    form_class = EquipmentForm
    template_name = 'maintenance/equipment_form.html'
    success_url = reverse_lazy('equipment_list')

    def test_func(self):
        equipment = self.get_object()
        return self.request.user == equipment.created_by or self.request.user.is_superuser

    def form_valid(self, form):
        messages.success(self.request, 'Equipment updated successfully.')
        return super().form_valid(form)

class EquipmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Equipment
    template_name = 'maintenance/equipment_confirm_delete.html'
    success_url = reverse_lazy('equipment_list')

    def test_func(self):
        equipment = self.get_object()
        return self.request.user == equipment.created_by or self.request.user.is_superuser

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Equipment deleted successfully.')
        return super().delete(request, *args, **kwargs)

class MaintenanceLogCreateView(LoginRequiredMixin, CreateView):
    model = MaintenanceLog
    form_class = MaintenanceLogForm
    template_name = 'maintenance/maintenance_log_form.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.performed_by = self.request.user
        response = super().form_valid(form)

        Notification.objects.create(
            user=self.request.user,
            notification_type='log_created',
            title='Maintenance Log Created',
            message=f'You recorded maintenance for {form.instance.equipment.name}. Time taken: {form.instance.time_taken_minutes} minutes.',
            link=f'/equipment/{form.instance.equipment.id}/'
        )

        messages.success(self.request, 'Maintenance log created successfully.')
        return response

class MaintenanceLogListView(LoginRequiredMixin, ListView):
    model = MaintenanceLog
    template_name = 'maintenance/maintenance_log_list.html'
    context_object_name = 'logs'
    paginate_by = 30

    def get_queryset(self):
        queryset = super().get_queryset()
        equipment_id = self.request.GET.get('equipment', '')
        activity_type = self.request.GET.get('type', '')
        search = self.request.GET.get('search', '')

        if equipment_id:
            queryset = queryset.filter(equipment_id=equipment_id)
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search) |
                Q(parts_replaced__icontains=search) |
                Q(equipment__name__icontains=search)
            )
        return queryset.select_related('equipment', 'performed_by').order_by('-date_performed')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activity_types'] = MaintenanceLog.ACTIVITY_TYPES
        context['equipment_list'] = Equipment.objects.all().order_by('name')
        context['current_equipment'] = self.request.GET.get('equipment', '')
        context['current_type'] = self.request.GET.get('type', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context

class MaintenanceLogDetailView(LoginRequiredMixin, DetailView):
    model = MaintenanceLog
    template_name = 'maintenance/maintenance_log_detail.html'
    context_object_name = 'log'

class MultimediaUploadView(LoginRequiredMixin, CreateView):
    model = Multimedia
    form_class = MultimediaForm
    template_name = 'maintenance/multimedia_upload.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'File uploaded successfully.')
        return response

class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'maintenance/message_list.html'
    context_object_name = 'inbox_messages'
    paginate_by = 20

    def get_queryset(self):
        return Message.objects.filter(recipient=self.request.user).select_related('sender').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sent_messages'] = Message.objects.filter(sender=self.request.user).order_by('-created_at')[:10]
        return context

class MessageDetailView(LoginRequiredMixin, DetailView):
    model = Message
    template_name = 'maintenance/message_detail.html'
    context_object_name = 'message'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if not self.object.is_read and self.object.recipient == request.user:
            self.object.is_read = True
            self.object.save()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reply_form'] = ReplyMessageForm()
        context['replies'] = self.object.replies.all()
        return context

class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'maintenance/message_form.html'
    success_url = reverse_lazy('message_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.sender = self.request.user
        response = super().form_valid(form)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{form.instance.recipient.id}',
            {
                'type': 'send_notification',
                'notification': {
                    'title': 'New Message',
                    'message': f'You have a new message from {self.request.user.username}: {form.instance.subject[:50]}',
                    'link': f'/messages/{self.object.id}/'
                }
            }
        )

        Notification.objects.create(
            user=form.instance.recipient,
            notification_type='message_received',
            title='New Message',
            message=f'Message from {self.request.user.username}: {form.instance.subject}',
            link=f'/messages/{self.object.id}/'
        )

        messages.success(self.request, 'Message sent successfully.')
        return response


class ReplyMessageView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = ReplyMessageForm
    template_name = 'maintenance/message_reply.html'

    def dispatch(self, request, *args, **kwargs):
        self.parent_message = get_object_or_404(Message, id=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parent_message'] = self.parent_message
        return context

    def form_valid(self, form):
        form.instance.sender = self.request.user
        form.instance.recipient = self.parent_message.sender
        form.instance.subject = f"Re: {self.parent_message.subject}"
        form.instance.parent_message = self.parent_message
        response = super().form_valid(form)

        Notification.objects.create(
            user=form.instance.recipient,
            notification_type='message_received',
            title='New Message Reply',
            message=f'{self.request.user.username} replied to your message: {form.instance.subject}',
            link=f'/messages/{self.object.id}/'
        )

        messages.success(self.request, 'Reply sent successfully.')
        return response

    def get_success_url(self):
        return reverse_lazy('message_detail', kwargs={'pk': self.parent_message.id})



        
class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'maintenance/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 30

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

class MarkNotificationReadView(LoginRequiredMixin, UpdateView):
    model = Notification
    fields = []
    template_name = None

    def post(self, request, *args, **kwargs):
        notification = self.get_object()
        if notification.user == request.user:
            notification.is_read = True
            notification.save()
        return JsonResponse({'status': 'ok'})

class MarkAllNotificationsReadView(LoginRequiredMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'ok'})

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'maintenance/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['equipment_created'] = Equipment.objects.filter(created_by=user).count()
        context['logs_created'] = MaintenanceLog.objects.filter(performed_by=user).count()
        context['messages_sent'] = Message.objects.filter(sender=user).count()
        context['multimedia_uploaded'] = Multimedia.objects.filter(uploaded_by=user).count()
        return context



class RecordMediaView(LoginRequiredMixin, TemplateView):
    template_name = 'maintenance/record_media.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['equipment_list'] = Equipment.objects.all().order_by('name')
        return context


class UploadRecordingView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            uploaded_file = request.FILES.get('file')
            equipment_id = request.POST.get('equipment_id')
            media_type = request.POST.get('media_type')
            description = request.POST.get('description', '')
            maintenance_log_id = request.POST.get('maintenance_log_id')
            
            if not uploaded_file:
                return JsonResponse({'status': 'error', 'message': 'No file uploaded'})
            
            if not equipment_id:
                return JsonResponse({'status': 'error', 'message': 'No equipment selected'})
            
            try:
                equipment = Equipment.objects.get(id=equipment_id)
            except Equipment.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Equipment not found'})
            
            maintenance_log = None
            if maintenance_log_id:
                try:
                    maintenance_log = MaintenanceLog.objects.get(id=maintenance_log_id, equipment=equipment)
                except MaintenanceLog.DoesNotExist:
                    pass
            
            multimedia = Multimedia.objects.create(
                equipment=equipment,
                maintenance_log=maintenance_log,
                media_type=media_type,
                file=uploaded_file,
                description=description,
                uploaded_by=request.user
            )
            
            Notification.objects.create(
                user=request.user,
                notification_type='log_created',
                title='Recording Uploaded',
                message=f'Recording for {equipment.name} has been uploaded',
                link=f'/equipment/{equipment.id}/'
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Recording saved successfully',
                'media_id': multimedia.id
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})