from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse


class Recipe(models.Model):
    """Модель рецепта."""
    name = models.CharField('Название рецепта', max_length=200)
    text = models.TextField('Описание')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    image = models.ImageField('Фото', upload_to='images/')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[MinValueValidator(
            1, message='Время приготовления должно быть больше 1 минуты.')],
    )
    tags = models.ManyToManyField('Tag')
    ingredients = models.ManyToManyField(
        'Ingredient', through='RecipeIngredient'
    )
    created = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        ordering = ['-created', 'name']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = [
            models.UniqueConstraint(fields=['name', 'author'],
                                    name='unique_recipe_author')
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('recipe-detail', kwargs={'recipe_id': self.pk})


class Tag(models.Model):
    """Модель тега для рецептов."""
    name = models.CharField('Имя тега', max_length=200, unique=True)
    color = models.CharField(
        'Цветовой HEX-код', max_length=7, null=True, unique=True)
    slug = models.SlugField(
        max_length=200, unique=True, null=True, db_index=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tag-detail', kwargs={'tag_id': self.pk})


class Ingredient(models.Model):
    """Модель ингредиента для рецептов."""
    name = models.CharField('Название', max_length=200)
    measurement_unit = models.CharField('Ед. изм.', max_length=200)

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, ({self.measurement_unit})'

    def get_absolute_url(self):
        return reverse('ingredient-detail', args=self.pk)


class RecipeIngredient(models.Model):
    """Промежуточная модель для связи рецепта и ингредиента."""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT)
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[MinValueValidator(
            1, message='Количество должно быть больше нуля.')]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['ingredient', 'recipe'],
                                    name='unique_ingredient_recipe')
        ]

    def __str__(self):
        return f'{self.recipe}: {self.ingredient}'


class Favorite(models.Model):
    """Модель для связи избранного рецепта и пользователя."""
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorites')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='favorites')

    class Meta:
        ordering = ['recipe', 'user']
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_user_favorite_recipe')
        ]

    def __str__(self):
        return '{self.user}: {self.recipe}'


class ShoppingCart(models.Model):
    """Модель связывает пользователя и добавленные в корзину рецепты."""
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='shopping_cart')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='shopping_cart')

    class Meta:
        ordering = ['recipe', 'user']
        verbose_name = 'Рецепт из списка покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_user_recipe_in_cart')
        ]

    def __str__(self):
        return '{self.user}: {self.recipe}'
