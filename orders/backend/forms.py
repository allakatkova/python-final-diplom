from django import forms
from backend.models import ShopFiles


class UploadFileForm(forms.ModelForm):
    class Meta:
        model = ShopFiles
        fields = ['file']
