from django import forms
from django.forms import inlineformset_factory
from .models import Recipe, Ingredient, Instruction


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ["title", "description", "prep_time", "cook_time", "servings"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ["name", "quantity", "unit"]


IngredientFormSet = inlineformset_factory(
    Recipe,
    Ingredient,
    form=IngredientForm,
    extra=0,
    can_delete=True,
)


class InstructionForm(forms.ModelForm):
    class Meta:
        model = Instruction
        fields = ["description"]


InstructionFormSet = inlineformset_factory(
    Recipe,
    Instruction,
    form=InstructionForm,
    extra=0,
    can_delete=True,
)
