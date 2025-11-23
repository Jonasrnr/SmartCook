from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
import json

from .models import Recipe, Ingredient, Instruction, Friend, Collection, UserProfile
from services.RecipeExtractor import RecipeExtractor
from services.getTikTokDesc import getTikTokDesc
from services.getInstaDesc import getInstaDesc
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
                if "instagram.com" in link:
                    description, thumbnail = getInstaDesc(link)
                elif "tiktok.com" in link:
                    description, thumbnail = getTikTokDesc(link)
                else:
                    toast_message = f"Es werden nur TikTok und Instagram-URLs unterstützt."
                    response = HttpResponse(status=204)
                    response['HX-Trigger'] = json.dumps({"show-toast": {"message": toast_message, "type": "error"}})
                    return response

                if not description or not thumbnail:
                    toast_message = f"Fehler beim Extrahieren der Video Beschreibung"
                    response = HttpResponse(status=204)
                    response['HX-Trigger'] = json.dumps({
                        "show-toast": {"message": toast_message, "type": "error"},
                    })
                    return response

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
                            original_creator=request.user,
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
                                recipe=recipe, step_number=i + 1, description=desc.strip()
                            )
                        
                        toast_message = f"Rezept wurde erfolgreich hinzugefügt"
                        response = HttpResponse(status=204)
                        response['HX-Trigger'] = json.dumps({
                            "show-toast": {"message": toast_message, "type": "success"},
                            "reload-content": True
                        })
                        return response
                    else:
                        message = "Keine Recipe-Extraction gefunden."

                else:
                    toast_message = f"Fehler beim Extrahieren des Rezepts aus der Beschreibung."
                    response = HttpResponse(status=204)
                    response['HX-Trigger'] = json.dumps({
                        "show-toast": {"message": toast_message, "type": "error"},
                    })
                    return response

            # TODO: Error Messages
            except Exception as e:
                toast_message = e
                response = HttpResponse(status=204)
                response['HX-Trigger'] = json.dumps({
                    "show-toast": {"message": toast_message, "type": "error"},
                    "reload-content": True
                })
                return response
        return render(request, "recipes/landing_page.html", {"message": message})
    return render(request, "recipes/landing_page.html")


@login_required
def profile_view(request, user_id=None):
    if user_id:
        profile_user = get_object_or_404(User, id=user_id)
    else:
        profile_user = request.user

    is_private = not getattr(profile_user, 'userprofile', None) or not profile_user.userprofile.public_profile
    if is_private and profile_user != request.user and request.headers.get("HX-Request") == "true":
        toast_message = f"Das Profil von {profile_user.username} ist privat."
        response = HttpResponse(status=204)
        response['HX-Trigger'] = json.dumps({"show-toast": toast_message})
        return response

    if request.method == "POST":
        print("TEST")
        if profile_user != request.user:
            return JsonResponse({"status": "error", "message": "Unauthorized"}, status=403)
        user_profile = get_object_or_404(UserProfile, user=request.user)

        is_checked = 'public_profile' in request.POST
        user_profile.public_profile = is_checked
        user_profile.save(update_fields=['public_profile'])

        new_text = "Profil öffentlich" if is_checked else "Profil privat"
        html = f'<span id="profile-status-text" class="text-sm font-medium text-gray-600">{new_text}</span>'
        return HttpResponse(html)

    if profile_user == request.user:
        recipes = Recipe.objects.filter(user=profile_user).order_by("-id")
    else:
        recipes = Recipe.objects.filter(user=profile_user).order_by("-id")

    if request.headers.get("HX-Request") == "true":
        return render(
            request,
            "recipes/partials/profile_partial.html",
            {"user": profile_user, "recipes": recipes},
        )
    return render(
        request,
        "recipes/profile.html",
        {"user": profile_user, "recipes": recipes},
    )


@login_required
def landing_page(request):
    recipes = Recipe.objects.filter(user=request.user).order_by("-id")

    if request.headers.get("HX-Request") == "true":
        return render(request, "recipes/partials/landing_page_partial.html", {"recipes": recipes})

    return render(request, "recipes/landing_page.html", {"recipes": recipes})


@login_required
def recipe_detail(request, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id)

    is_own_recipe = recipe.user == request.user
    is_friend_recipe = request.user.friend_profile.friends.filter(id=recipe.user.id).exists()

    if not (is_own_recipe or is_friend_recipe):
        return redirect("landing_page")
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
    if request.headers.get("HX-Request") == "true":
        return render(request, "recipes/partials/recipe_detail_partial.html", context)
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
    if request.headers.get("HX-Request") == "true":
        return render(request, "recipes/partials/recipe_edit_partial.html", context)
    return render(request, "recipes/recipe_edit.html", context)


@require_POST
@login_required
def update_recipe(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            recipe_id = data.get("id")
            field = data.get("field")
            value = data.get("value")

            recipe = get_object_or_404(Recipe, pk=recipe_id, user=request.user)

            if field in ["prep_time", "cook_time", "servings"] and value == "":
                value = None

            setattr(recipe, field, value)
            recipe.save()

            return JsonResponse({"status": "ok"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)


@require_POST
@login_required
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
@login_required
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


@login_required
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

@login_required
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
def add_recipe_from_friend(request, recipe_id):
    original_recipe = get_object_or_404(Recipe, pk=recipe_id)

    if original_recipe.user == request.user:
        messages.info(request, "Du kannst deine eigenen Rezepte nicht kopieren.")
        return redirect("recipe_detail", recipe_id=original_recipe.id)

    new_recipe = Recipe.objects.create(
        user=request.user,
        original_creator=original_recipe.user,
        title=original_recipe.title,
        description=original_recipe.description,
        prep_time=original_recipe.prep_time,
        cook_time=original_recipe.cook_time,
        servings=original_recipe.servings,
        thumbnail=original_recipe.thumbnail,
        url=original_recipe.url,
    )

    for ing in original_recipe.ingredients.all():
        Ingredient.objects.create(recipe=new_recipe, name=ing.name, quantity=ing.quantity, unit=ing.unit)

    for instr in original_recipe.instruction_steps.all():
        Instruction.objects.create(recipe=new_recipe, step_number=instr.step_number, description=instr.description)

    return redirect("recipe_detail", recipe_id=new_recipe.id)

@login_required
def friends_view(request):
    friend_profile = request.user.friend_profile
    friends = friend_profile.friends.all()
    all_users = User.objects.exclude(id=request.user.id)
    public_users = all_users.filter(userprofile__public_profile=True)

    potential_friends = public_users.exclude(id__in=friends.values_list("id", flat=True), )
    if request.headers.get("HX-Request") == "true":
        return render(
            request,
            "recipes/partials/friends_partial.html",
            {"friends": friends, "potential_friends": potential_friends}
        )
    
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
    if request.headers.get("HX-Request") == "true":
        return render(request, "recipes/partials/collections_partial.html", context)
    return render(request, "recipes/collections.html", context)

@login_required
def collection_detail(request, collection_id):
    collection = get_object_or_404(Collection, pk=collection_id, user=request.user)
    recipes = collection.recipes.all()

    context = {
        "collection": collection,
        "recipes": recipes,
    }
    if request.headers.get("HX-Request") == "true":
        return render(request, "recipes/partials/collection_detail_partial.html", context)

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
    recipe = get_object_or_404(Recipe, pk=recipe_id)
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
    if request.headers.get("HX-Request") == "true":
        return render(request, "recipes/partials/search_partial.html", {"query": query, "recipes": recipes})
    return render(request, "recipes/search.html", {"query": query, "recipes": recipes})