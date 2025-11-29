from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Experiment

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class ExperimentForm(forms.ModelForm):
    """Form for creating new experiments (admin only)."""
    
    class Meta:
        model = Experiment
        fields = ['name', 'description', 'url', 'port']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'e.g., Exp#6 Custom Setup',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Describe the purpose and functionality of this experiment',
                'rows': 4,
                'required': True
            }),
            'url': forms.URLInput(attrs={
                'placeholder': 'http://10.7.43.20',
                'required': True
            }),
            'port': forms.NumberInput(attrs={
                'placeholder': '8080',
                'min': 1,
                'max': 65535,
                'required': True
            }),
        }
    
    def clean_port(self):
        """Validate port is in valid range."""
        port = self.cleaned_data.get('port')
        if port and (port < 1 or port > 65535):
            raise forms.ValidationError("Port must be between 1 and 65535.")
        return port
    
    def save(self, commit=True):
        """Auto-generate exp_key and set is_custom flag."""
        experiment = super().save(commit=False)
        
        # Auto-generate exp_key based on name
        name = experiment.name
        base_key = name.lower().replace(' ', '_').replace('#', '')[:20]
        
        # Ensure uniqueness
        key = base_key
        counter = 1
        while Experiment.objects.filter(exp_key=key).exists():
            key = f"{base_key}_{counter}"
            counter += 1
        
        experiment.exp_key = key
        experiment.is_custom = True
        
        if commit:
            experiment.save()
        return experiment