from collections import defaultdict

from django.shortcuts import get_object_or_404
from rest_framework import status

from api.serializers import RecipeListSerializer
from recipes.models import Recipe


def create_shopping_list(queryset) -> list:
    """Создает список покупок на основе переданного QuerySet.
    QuerySet должен быть списком объектов модели RecipeIngredient.
    Вид элемента списка:
    "- название ингредиента (ед.изм.): количество"
    """
    data = defaultdict(int)
    for ingr in queryset:
        key = (f'{ingr["ingredient__name"]} '
               f'({ingr["ingredient__measurement_unit"]})')
        data[key] += ingr['amount']
    shopping_list = ['СПИСОК ПОКУПОК:\n']
    for key, value in data.items():
        shopping_list.append(f'- {key}: {value} \n')
    return shopping_list


def add_obj(request, pk, model):
    """Вспомогательная функция для RecipeViewSet.
    Создает связь между рецептом и пользователем через модель.
    Параметры:
    request -- запрос
    pk -- id рецепта
    model -- промежуточная модель для создания связи с рецептом
    Возвращает кортеж из двух элементов:
    - подготовленные данные для ответа
    - статус ответа
    """
    recipe = get_object_or_404(Recipe, pk=pk)
    _, created = model.objects.get_or_create(
        recipe=recipe, user=request.user)
    if not created:
        return ({"errors": f"У вас уже добавлен рецепт с id {pk}."},
                status.HTTP_400_BAD_REQUEST)
    serializer = RecipeListSerializer(recipe, context={'request': request})
    return (serializer.data, status.HTTP_201_CREATED)


def del_obj(request, pk, model):
    """Вспомогательная функция для RecipeViewSet.
    Уничтожает связь между рецептом и пользователем через модель.
    Параметры:
    request -- запрос
    pk -- id рецепта
    model -- промежуточная модель для создания связи с рецептом
    Возвращает кортеж из двух элементов:
    - подготовленные данные для ответа
    - статус ответа
    """
    recipe = get_object_or_404(Recipe, pk=pk)
    fav_recipe = get_object_or_404(model, recipe=recipe, user=request.user)
    fav_recipe.delete()
    return ({"success": f"Рецепта с id {pk} удален."},
            status.HTTP_204_NO_CONTENT)
