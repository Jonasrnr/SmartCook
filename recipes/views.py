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

from .models import Recipe, Ingredient, Instruction, Friend, Collection
from services.RecipeExtractor import RecipeExtractor
from services.getTikTokDesc import getTikTokDesc
from services.searchRecipes import searchRecipes
from .forms import (
    RecipeForm,
    IngredientFormSet,
    CollectionForm,
    InstructionFormSet,
    UserSignupForm,
    UserLoginForm,
)


def signup_view(request):
    if request.method == "POST":
        form = UserSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            Friend.objects.create(user=user)
            messages.success(
                request, "Account erfolgreich erstellt! Du kannst dich jetzt einloggen."
            )
            return redirect("login")
    else:
        form = UserSignupForm()
    return render(request, "recipes/signup.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("landing_page")
    else:
        form = UserLoginForm()
    return render(request, "recipes/login.html", {"form": form})


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
                print("annotated_doc:", annotated_doc)

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

            # TODO: Error Messages
            except Exception as e:
                message = f"Fehler: {e}"
        return render(request, "recipes/landing_page.html", {"message": message})
    return render(request, "recipes/landing_page.html")


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
    recipes = Recipe.objects.filter(user=request.user).order_by("-id")
    return render(request, "recipes/landing_page.html", {"recipes": recipes})


@login_required
def recipe_detail(request, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id, user=request.user)
    user_collections = Collection.objects.filter(user=request.user)
    collections_with_recipe = list(user_collections.filter(recipes=recipe).values_list('id', flat=True))

    ingredients = recipe.ingredients.all()
    instructions = recipe.instruction_steps.all()

    context = {
        "recipe": recipe,
        "ingredients": ingredients,
        "instructions": instructions,
        "collections": user_collections,
        "collections_with_recipe": collections_with_recipe,
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
def collections_view(request):
    if request.method == "POST":
        form = CollectionForm(request.POST)
        if form.is_valid():
            collection = form.save(commit=False)
            collection.user = request.user
            collection.save()
            messages.success(request, f"Sammlung '{collection.name}' wurde erstellt.")
            return redirect("collections")
    else:
        form = CollectionForm()

    collections = Collection.objects.filter(user=request.user).order_by("-id")
    context = {
        "form": form,
        "collections": collections,
    }
    return render(request, "recipes/collections.html", context)

@login_required
def collection_detail(request, collection_id):
    collection = get_object_or_404(Collection, pk=collection_id, user=request.user)
    recipes = collection.recipes.all()

    context = {
        "collection": collection,
        "recipes": recipes,
    }
    return render(request, "recipes/collection_detail.html", context)

@login_required
def remove_friend(request, friend_id):
    friend_profile = request.user.friend_profile
    friend_to_remove = get_object_or_404(User, id=friend_id)
    friend_profile.friends.remove(friend_to_remove)
    return redirect("friends")


@login_required
@require_POST
def refresh_thumbnail(request, recipe_id):
    print("test")
    recipe = get_object_or_404(Recipe, pk=recipe_id, user=request.user)
    if not recipe.url:
        return JsonResponse({"status": "error", "message": "No TikTok URL for this recipe."}, status=400)

    try:
        _, new_thumbnail_url = getTikTokDesc(recipe.url)
        if new_thumbnail_url:
            recipe.thumbnail = new_thumbnail_url
            recipe.save(update_fields=['thumbnail'])
            return JsonResponse({"status": "ok", "thumbnail_url": new_thumbnail_url})
        else:
            return JsonResponse({"status": "error", "message": "Could not retrieve new thumbnail."}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@login_required
@require_POST
def add_recipe_to_collection(request):
    try:
        data = json.loads(request.body)
        recipe_id = data.get("recipe_id")
        collection_id = data.get("collection_id")

        recipe = get_object_or_404(Recipe, pk=recipe_id, user=request.user)
        collection = get_object_or_404(Collection, pk=collection_id, user=request.user)

        if recipe in collection.recipes.all():
            return JsonResponse({"status": "info", "message": "Rezept ist bereits in dieser Sammlung."})

        collection.recipes.add(recipe)
        return JsonResponse({"status": "ok", "message": f"Rezept zu '{collection.name}' hinzugefügt."})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@login_required
@require_POST
def remove_recipe_from_collection(request):
    try:
        data = json.loads(request.body)
        recipe_id = data.get("recipe_id")
        collection_id = data.get("collection_id")

        recipe = get_object_or_404(Recipe, pk=recipe_id, user=request.user)
        collection = get_object_or_404(Collection, pk=collection_id, user=request.user)

        collection.recipes.remove(recipe)
        return JsonResponse({"status": "ok", "message": f"Rezept aus '{collection.name}' entfernt."})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

@login_required
def search_view(request):
    query = request.GET.get("q", "").strip()
    results = []
    recipes = Recipe.objects.filter(user=request.user)
    if query:
        results = searchRecipes(query, recipes)
        recipes = [recipe for recipe, score in results]
        print(recipes)
    return render(request, "recipes/search.html", {"query": query, "recipes": recipes})