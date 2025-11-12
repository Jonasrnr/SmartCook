#https://github.com/rapidfuzz/RapidFuzz
from rapidfuzz import process, fuzz

def searchRecipes(query, recipe_list):
    terms = query.split()
    results = []
    for recipe in recipe_list:
        ingredient_names = [ingredient.name for ingredient in recipe.ingredients.all()]

        scores = []

        for term in terms:
            title_score = fuzz.partial_ratio(term.lower(), recipe.title.lower())
            ingredient_score = max(
                [fuzz.partial_ratio(term.lower(), name.lower()) for name in ingredient_names] + [0]
            )
            scores.append(max(title_score, ingredient_score))

        for score in scores:    
            if all(score >= 70 for score in scores):
                avg_score = sum(scores) / len(scores)
                if recipe not in [r for r, s in results]:
                    results.append((recipe, avg_score))
                

    results = sorted(results, key=lambda x: x[1], reverse=True)

    return results