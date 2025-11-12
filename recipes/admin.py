from django.contrib import admin
from .models import Recipe, Ingredient, Instruction, Collection

admin.site.register_collection = admin.site.register(Recipe)
admin.site.register(Ingredient)
admin.site.register(Instruction)
admin.site.register(Collection)