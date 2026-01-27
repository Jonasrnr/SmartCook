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
        self.fields["username"].widget.attrs.update(
            {
                "class": "border-black border-2 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
            }
        )
        self.fields["password"].widget.attrs.update(
            {
                "class": "border-black border-2 rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
            }
        )


IngredientFormSet = forms.inlineformset_factory(
    Recipe, Ingredient, fields=("name", "quantity", "unit"), extra=1
)

InstructionFormSet = forms.inlineformset_factory(
    Recipe, Instruction, fields=("step_number", "description"), extra=1
)


class RecipeForm(forms.ModelForm):
    image = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={
        "class": "border rounded-md px-3 py-2 w-full"
    }))

    class Meta:
        model = Recipe
        exclude = ["user", "original_creator"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "border rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-500",
                "placeholder": "Titel des Rezepts"
            }),
            "description": forms.Textarea(attrs={
                "class": "border rounded-md px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-500",
                "placeholder": "Beschreibung",
                "rows": 4
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        formset_kwargs = kwargs.copy()
        formset_kwargs.pop("instance", None)
        self.ingredient_formset = IngredientFormSet(*args, **formset_kwargs, instance=self.instance, prefix="ingredients")
        self.instruction_formset = InstructionFormSet(*args, **formset_kwargs, instance=self.instance, prefix="instructions")

    def is_valid(self):
        return super().is_valid() and self.ingredient_formset.is_valid() and self.instruction_formset.is_valid()

    def save(self, commit=True):
        recipe = super().save(commit=commit)
        if commit:
            self.ingredient_formset.instance = recipe
            self.ingredient_formset.save()
            self.instruction_formset.instance = recipe
            self.instruction_formset.save()
        return recipe


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'flex-grow px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600', 'placeholder': 'Name der Sammlung'}),
            'description': forms.Textarea(attrs={'class': 'flex-grow px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600', 'placeholder': 'Beschreibung (optional)', 'rows': 3}),
        }