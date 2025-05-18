from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.core.validators import validate_email

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        validators=[validate_email],
        help_text="Required. Enter a valid email address."
    )
    
    class Meta(UserCreationForm.Meta):
        fields = ('username', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            if field.required:
                field.label = f"{field.label}*"
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and self._meta.model.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email