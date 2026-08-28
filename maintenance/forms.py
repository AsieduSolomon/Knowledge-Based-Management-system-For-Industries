from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Equipment, MaintenanceLog, Multimedia, Message

class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ['name', 'equipment_type', 'location', 'manufacturer', 'model_number', 'installation_date', 'notes']
        widgets = {
            'installation_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class MaintenanceLogForm(forms.ModelForm):
    class Meta:
        model = MaintenanceLog
        fields = ['equipment', 'activity_type', 'date_performed', 'description', 'parts_replaced', 'time_taken_minutes']
        widgets = {
            'date_performed': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'parts_replaced': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['equipment'].queryset = Equipment.objects.all().order_by('name')

class MultimediaForm(forms.ModelForm):
    class Meta:
        model = Multimedia
        fields = ['equipment', 'media_type', 'file', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        media_type = self.cleaned_data.get('media_type')
        
        if file and media_type:
            file_extension = file.name.split('.')[-1].lower()
            
            if media_type == 'audio':
                allowed = ['mp3', 'wav', 'm4a', 'ogg']
                if file_extension not in allowed:
                    raise forms.ValidationError(f'Audio files must be one of: {", ".join(allowed)}')
                if file.size > 50 * 1024 * 1024:
                    raise forms.ValidationError('Audio files must be smaller than 50MB')
                    
            elif media_type == 'video':
                allowed = ['mp4', 'webm', 'mov', 'avi']
                if file_extension not in allowed:
                    raise forms.ValidationError(f'Video files must be one of: {", ".join(allowed)}')
                if file.size > 200 * 1024 * 1024:
                    raise forms.ValidationError('Video files must be smaller than 200MB')
                    
            elif media_type in ['image', 'diagram']:
                allowed = ['jpg', 'jpeg', 'png', 'gif', 'webp']
                if file_extension not in allowed:
                    raise forms.ValidationError(f'Image files must be one of: {", ".join(allowed)}')
                if file.size > 10 * 1024 * 1024:
                    raise forms.ValidationError('Image files must be smaller than 10MB')
                    
        return file
class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['recipient'].queryset = User.objects.exclude(id=self.user.id)

class ReplyMessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 4}),
        }

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']