from django.db import models
from django.contrib.auth.models import User


class Recipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    prep_time = models.CharField(max_length=50, null=True, blank=True)
    cook_time = models.CharField(max_length=50, null=True, blank=True)
    servings = models.CharField(max_length=50, null=True, blank=True)
    thumbnail = models.CharField(max_length=200, null=True, blank=True)
    url = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.title


class Ingredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, related_name="ingredients", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    quantity = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        parts = []
        if self.quantity is not None:
            parts.append(str(self.quantity))
        if self.unit:
            parts.append(self.unit)
        parts.append(self.name)
        return " ".join(parts)


class Instruction(models.Model):
    recipe = models.ForeignKey(
        Recipe, related_name="instruction_steps", on_delete=models.CASCADE
    )
    step_number = models.PositiveIntegerField()
    description = models.TextField()

    class Meta:
        ordering = ["step_number"]


class Friend(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="friend_profile"
    )
    friends = models.ManyToManyField(User, related_name="friends", blank=True)

    def __str__(self):
        return f"{self.user.username}'s Freunde"
