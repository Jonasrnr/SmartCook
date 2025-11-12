from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

from .models import Recipe, Ingredient, Instruction, Collection


class UserSignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Diese E-Mail-Adresse wird bereits verwendet.")
        return email


class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = "__all__"


IngredientFormSet = forms.inlineformset_factory(
    Recipe, Ingredient, fields=("name", "quantity", "unit"), extra=0
)
InstructionFormSet = forms.inlineformset_factory(
    Recipe, Instruction, fields=("description",), extra=0
)
class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'flex-grow px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600', 'placeholder': 'Name der Sammlung'}),
            'description': forms.Textarea(attrs={'class': 'flex-grow px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600', 'placeholder': 'Beschreibung (optional)', 'rows': 3}),
        }