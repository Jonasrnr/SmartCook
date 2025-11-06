from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("landing_page/", views.landing_page, name="landing_page"),
    path("add/", views.recipe_input, name="recipe_input"),
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),
    path("recipe/<int:recipe_id>/", views.recipe_detail, name="recipe_detail"),
    path("recipe/<int:recipe_id>/edit/", views.recipe_edit, name="recipe_edit"),
    path("recipe/<int:recipe_id>/delete/", views.recipe_delete, name="recipe_delete"),
    path("update_ingredient/", views.update_ingredient, name="update_ingredient"),
    path("update_instruction/", views.update_instruction, name="update_instruction"),
    path(
        "add_ingredient/<int:recipe_id>/",
        views.add_ingredient,
        name="add_ingredient",
    ),
    path(
        "add_instruction/<int:recipe_id>/",
        views.add_instruction,
        name="add_instruction",
    ),
    path("profile/", views.profile_view, name="profile"),
    path("profile/<int:user_id>/", views.profile_view, name="profile_view"),
    path("friends/", views.friends_view, name="friends"),
    path("friends/add/<int:friend_id>/", views.add_friend, name="add_friend"),
    path("friends/remove/<int:friend_id>/", views.remove_friend, name="remove_friend"),
]
