from collections import defaultdict

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription
from .filters import RecipeFilter
from .permissions import OwnerOrReadOnly, ReadOnly
from .serializers import (IngredientSerializer, RecipeListSerializer,
                          RecipeSerializer, SubscriptionSerializer,
                          TagSerializer)

User = get_user_model()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    retrieve: Возвращает запрашиваемый ингредиент.
    list: Возвращает все ингредиенты.
    Доступен поиск по названию ингридиента.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (ReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class TagViewSet(viewsets.ModelViewSet):
    """
    retrieve: Возвращает запрашиваемый тег.
    list: Возвращает все теги.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (ReadOnly,)


class RecipeViewSet(viewsets.ModelViewSet):
    """
    retrieve: Возвращает запрашиваемый рецепт.
              Доступ не ограничен.
    list: Возвращает все рецепты.
          Доступ не ограничен.
    create: Создаст новый объект - рецепт.
            Доступ только авторизованным пользователям.
    update: Изменение объекта.
            Частичное изменение запрещено.
            Доступ только авторизованныму автору рецепта.
    destroy: Удаление объекта.
             Доступ только авторизованныму автору рецепта.
    filters: Доступна фильтрация по полям:
             - author,
             - tags,
             - is_favorite,
             - is_in_shopping_cart
    """
    queryset = Recipe.objects.prefetch_related(
                'author', 'tags', 'ingredients').all()
    serializer_class = RecipeSerializer
    permission_classes = (OwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = PageNumberPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _add_obj(self, request, pk, model):
        """Вспомогательный метод.
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

    def _del_obj(self, request, pk, model):
        """Вспомогательный метод.
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

    @action(methods=['post', 'delete'], detail=True)
    def favorite(self, request, pk):
        """Добавляет/удаляет рецепт из Избранного текущего пользователя."""
        if request.method == "POST":
            data, status = self._add_obj(request, pk, Favorite)
            return Response(data, status=status)
        data, status = self._del_obj(request, pk, Favorite)
        return Response(data, status=status)

    @action(methods=['post', 'delete'], detail=True)
    def shopping_cart(self, request, pk):
        """Добавляет/удаляет рецепт из Списка покупок текущего пользователя."""
        if request.method == "POST":
            data, status = self._add_obj(request, pk, ShoppingCart)
            return Response(data, status=status)
        data, status = self._del_obj(request, pk, ShoppingCart)
        return Response(data, status=status)

    @action(methods=['get'], detail=False,
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Возвращает список покупок текущего пользователя в формате txt."""
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user).values(
                'ingredient__name',
                'ingredient__measurement_unit',
                'amount').order_by('ingredient__name')
        data = defaultdict(int)
        for ingr in ingredients:
            key = (f'{ingr["ingredient__name"]} '
                   f'({ingr["ingredient__measurement_unit"]})')
            data[key] += ingr['amount']
        shopping_list = ['СПИСОК ПОКУПОК:\n']
        for key, value in data.items():
            shopping_list.append(f'- {key}: {value} \n')
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename={0}'.format('shopping_list.txt')
        )
        return response


class UserViewSet(DjoserUserViewSet):
    serializer_class = SubscriptionSerializer
    pagination_class = PageNumberPagination

    @action(methods=['post'], detail=True,
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id):
        """Подписывает текущего пользователя на автора рецепта."""
        author = get_object_or_404(User, pk=id)
        if request.user == author:
            return Response(
                    {"errors": "Нельзя подписаться на самого себя."},
                    status=status.HTTP_400_BAD_REQUEST)
        _, created = Subscription.objects.get_or_create(
            author=author, subscriber=request.user)
        if not created:
            return Response(
                {"errors": "Вы уже подписаны на этого автора."},
                status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(
            author, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        """Отписывает текущего пользователя от автора рецепта."""
        author = get_object_or_404(User, pk=id)
        subscription = get_object_or_404(
            Subscription, author=author, subscriber=request.user)
        subscription.delete()
        return Response({"success": "Вы успешно отписаны."},
                        status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=False,
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Возвращает список авторов, на которых подписан пользователь."""
        authors = User.objects.filter(subscription__subscriber=request.user)
        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(
            authors, many=True, context={'request': request})
        return Response(serializer.data)
