from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

from .models import Recipe, Ingredient, Instruction
from services.RecipeExtractor import RecipeExtractor
from services.getTikTokDesc import getTikTokDesc
from .forms import RecipeForm, IngredientFormSet, InstructionFormSet


def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if not username or not email or not password1 or not password2:
            messages.error(request, "Alle Felder müssen ausgefüllt werden.")
            return render(request, "recipes/signup.html")

        if password1 != password2:
            messages.error(request, "Passwörter stimmen nicht überein.")
            return render(request, "recipes/signup.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Benutzername existiert bereits.")
            return render(request, "recipes/signup.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email existiert bereits.")
            return render(request, "recipes/signup.html")

        user = User.objects.create_user(
            username=username, email=email, password=password1
        )
        Friend.objects.create(user=user)
        user.save()

        messages.success(
            request, "Account erfolgreich erstellt! Du kannst dich jetzt einloggen."
        )
        return redirect("login")

    return render(request, "recipes/signup.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("landing_page")
        else:
            messages.error(request, "Benutzername oder Passwort ist falsch.")

    return render(request, "recipes/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def recipe_input(request):
    if request.method == "POST":
        link = request.POST.get("tiktok_link", "").strip()
        if link:
            try:
                description, thumbnail = getTikTokDesc(link)

                extractor = RecipeExtractor(api_key=settings.LANGEXTRACT_API_KEY)
                annotated_doc = extractor.extract_recipe(description)

                if annotated_doc and annotated_doc.extractions:
                    recipe_dict = None
                    for ex in annotated_doc.extractions:
                        if ex.extraction_class == "Recipe":
                            recipe_dict = json.loads(ex.extraction_text)
                            break

                    if recipe_dict:
                        recipe = Recipe.objects.create(
                            user=request.user,
                            title=recipe_dict.get("title", ""),
                            description=recipe_dict.get("description", ""),
                            prep_time=recipe_dict.get("prep_time", ""),
                            cook_time=recipe_dict.get("cook_time", ""),
                            servings=recipe_dict.get("servings", ""),
                            thumbnail=thumbnail,
                            url=link,
                        )
                        for ing in recipe_dict.get("ingredients", []):
                            Ingredient.objects.create(recipe=recipe, **ing)
                        for i, desc in enumerate(recipe_dict.get("instructions", [])):
                            Instruction.objects.create(
                                recipe=recipe, step_number=i + 1, description=desc
                            )
                        return redirect("landing_page")
                    else:
                        message = "Keine Recipe-Extraction gefunden."

                else:
                    message = "Fehler: Recipe konnte nicht extrahiert werden."

            except Exception as e:
                message = f"Fehler: {e}"
        return render(request, "recipes/form.html", {"message": message})
    return render(request, "recipes/form.html")


@login_required
def profile_view(request, user_id=None):
    if user_id:
        user = get_object_or_404(User, id=user_id)
    else:
        user = request.user

    if user == request.user:
        recipes = Recipe.objects.filter(user=user).order_by("-id")
    else:
        recipes = Recipe.objects.filter(user=user).order_by("-id")

    return render(
        request,
        "recipes/profile.html",
        {"user": user, "recipes": recipes},
    )


@login_required
def landing_page(request):
    print(request.user)
    recipes = Recipe.objects.filter(user=request.user).order_by("-id")
    return render(request, "recipes/landing_page.html", {"recipes": recipes})


@login_required
def recipe_detail(request, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id, user=request.user)

    ingredients = recipe.ingredients.all()
    instructions = recipe.instruction_steps.all()

    context = {
        "recipe": recipe,
        "ingredients": ingredients,
        "instructions": instructions,
    }
    return render(request, "recipes/recipe_detail.html", context)


@login_required
def recipe_edit(request, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id, user=request.user)

    form = RecipeForm(instance=recipe)
    ingredient_formset = IngredientFormSet(instance=recipe, prefix="ingredients")
    instruction_formset = InstructionFormSet(instance=recipe, prefix="instructions")

    context = {
        "recipe": recipe,
        "form": form,
        "ingredient_formset": ingredient_formset,
        "instruction_formset": instruction_formset,
    }
    return render(request, "recipes/recipe_edit.html", context)


@require_POST
def update_ingredient(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            ingredient_id = data.get("id")
            field = data.get("field")
            value = data.get("value")

            ingredient = get_object_or_404(
                Ingredient, pk=ingredient_id, recipe__user=request.user
            )

            if field == "quantity" and value == "":
                value = None

            setattr(ingredient, field, value)
            ingredient.save()

            ingredient.refresh_from_db()
            if (
                not ingredient.name
                and ingredient.quantity is None
                and not ingredient.unit
            ):
                ingredient_id_to_delete = ingredient.id
                ingredient.delete()
                return JsonResponse(
                    {"status": "deleted", "id": ingredient_id_to_delete}
                )

            return JsonResponse({"status": "ok"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)


@require_POST
def update_instruction(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            instruction_id = data.get("id")
            field = data.get("field")
            value = data.get("value")

            try:
                instruction = get_object_or_404(
                    Instruction, pk=instruction_id, recipe__user=request.user
                )
            except Instruction.DoesNotExist:
                return JsonResponse(
                    {"status": "error", "message": "Instruction not found"}, status=404
                )

            if field == "description" and not value.strip():
                recipe = instruction.recipe
                instruction_id_to_delete = instruction.id
                instruction.delete()

                remaining_instructions = recipe.instruction_steps.order_by(
                    "step_number"
                )
                for i, instr in enumerate(remaining_instructions):
                    instr.step_number = i + 1
                    instr.save()
                return JsonResponse(
                    {
                        "status": "deleted",
                        "id": instruction_id_to_delete,
                        "renumber": True,
                    }
                )

            setattr(instruction, field, value)
            instruction.save()
            return JsonResponse({"status": "ok"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)


@login_required
@require_POST
def recipe_delete(request, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id, user=request.user)
    recipe.delete()
    return redirect("landing_page")


def add_ingredient(request, recipe_id):
    if request.method == "POST":
        recipe = get_object_or_404(Recipe, pk=recipe_id, user=request.user)
        ingredient = Ingredient.objects.create(
            recipe=recipe, name="", quantity=None, unit=""
        )
        return JsonResponse({"status": "ok", "id": ingredient.id})
    return JsonResponse(
        {"status": "error", "message": "Nur POST-Anfragen erlaubt"}, status=400
    )


def add_instruction(request, recipe_id):
    if request.method == "POST":
        recipe = get_object_or_404(Recipe, pk=recipe_id, user=request.user)

        last_instruction = recipe.instruction_steps.order_by("step_number").last()
        if last_instruction and not last_instruction.description.strip():
            instruction = last_instruction
        else:
            new_step_number = recipe.instruction_steps.count() + 1
            instruction = Instruction.objects.create(
                recipe=recipe, description="", step_number=new_step_number
            )
        return JsonResponse(
            {
                "status": "ok",
                "id": instruction.id,
                "step_number": instruction.step_number,
            }
        )
    return JsonResponse(
        {"status": "error", "message": "Nur POST-Anfragen erlaubt"}, status=400
    )


@login_required
def friends_view(request):
    friend_profile = request.user.friend_profile
    friends = friend_profile.friends.all()
    all_users = User.objects.exclude(id=request.user.id)

    potential_friends = all_users.exclude(id__in=friends.values_list("id", flat=True))
    return render(
        request,
        "recipes/friends.html",
        {"friends": friends, "potential_friends": potential_friends},
    )


@login_required
def add_friend(request, friend_id):
    friend_profile = request.user.friend_profile
    new_friend = get_object_or_404(User, id=friend_id)
    if new_friend != request.user:
        friend_profile.friends.add(new_friend)
    return redirect("friends")


@login_required
def remove_friend(request, friend_id):
    friend_profile = request.user.friend_profile
    friend_to_remove = get_object_or_404(User, id=friend_id)
    friend_profile.friends.remove(friend_to_remove)
    return redirect("friends")
