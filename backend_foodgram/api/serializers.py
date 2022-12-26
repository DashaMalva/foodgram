import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription

User = get_user_model()


class RecipeListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('__all__',)


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        """Возвращает True если пользователь подписан на автора."""
        current_user = self.context.get('request').user
        if current_user.is_anonymous:
            return False
        return Subscription.objects.filter(
            author=obj, subscriber=current_user).exists()


class SubscriptionSerializer(UserSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count',)

    def get_recipes_count(self, obj):
        """Возвращает количество рецептов отслеживаемого автора."""
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj)
        if limit:
            recipes = recipes[:int(limit)]
        return RecipeListSerializer(recipes, many=True).data


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class Base64ImageField(serializers.ImageField):
    """Декодирует картинку из строки base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            name = {self.context["request"].user.username}
            data = ContentFile(base64.b64decode(imgstr), name=f'{name}.' + ext)
        return super().to_internal_value(data)


class RecipeSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(use_url=True)
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipeingredient_set', many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')

    def validate(self, data):
        for field in ('tags', 'ingredients', 'name', 'text', 'cooking_time'):
            if not self.initial_data.get(field):
                raise serializers.ValidationError(
                    f'Не заполнено поле `{field}`')
        ingredients = self.initial_data['ingredients']
        ingredients_ids = list()
        for ingredient in ingredients:
            if not ingredient.get('amount') or not ingredient.get('id'):
                raise serializers.ValidationError(
                    'Убедитесь, что поле `ингредиенты` заполнено верно.')
            if not int(ingredient['amount']) > 0:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть больше нуля.')
            if ingredient['id'] in ingredients_ids:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться.')
            ingredients_ids.append(ingredient['id'])
        return data

    def get_is_favorited(self, obj):
        """Возвращает True, если рецепт в Избранном пользователя."""
        current_user = self.context['request'].user
        if current_user.is_anonymous:
            return False
        return Favorite.objects.filter(
            recipe=obj, user=current_user).exists()

    def get_is_in_shopping_cart(self, obj):
        """Возвращает True, если рецепт в Списке покупок пользователя."""
        current_user = self.context['request'].user
        if current_user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            recipe=obj, user=current_user).exists()

    def _create_recipe_ingredient_objects(self, recipe, ingredients):
        """Вспомогательный метод.
        Принимает на вход объект рецепта и список ингредиентов.
        Создает объекты модели RecipeIngredient."""
        obj = (RecipeIngredient(
            recipe=recipe, ingredient_id=ing['id'], amount=ing['amount']
            ) for ing in ingredients)
        RecipeIngredient.objects.bulk_create(obj)

    def create(self, validated_data):
        tags = self.initial_data.get('tags')
        ingredients = self.initial_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self._create_recipe_ingredient_objects(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        ingredients = self.initial_data.pop('ingredients')
        RecipeIngredient.objects.filter(recipe=instance).all().delete()
        self._create_recipe_ingredient_objects(instance, ingredients)
        tags = self.initial_data.get('tags')
        instance.tags.set(tags)
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        instance.save()
        return instance
