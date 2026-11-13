from django.conf import settings
from django.db import models


class Genre(models.Model):
    """Жанр фильма (драма, комедия и т. д.)."""

    name = models.CharField('Название', max_length=50, unique=True)

    class Meta:
        db_table = 'genres'
        ordering = ['name']
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.name


class Movie(models.Model):
    """Фильм из общего каталога. Каталог ведёт администратор."""

    title = models.CharField('Название', max_length=200)
    year = models.PositiveSmallIntegerField('Год выхода')
    description = models.TextField('Описание', blank=True)
    poster_url = models.URLField('Постер', max_length=300, blank=True)
    genres = models.ManyToManyField(
        Genre, db_table='movie_genres', related_name='movies', verbose_name='Жанры'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='added_movies',
        verbose_name='Кто добавил',
    )
    created_at = models.DateTimeField('Добавлен', auto_now_add=True)

    class Meta:
        db_table = 'movies'
        ordering = ['title']
        verbose_name = 'Фильм'
        verbose_name_plural = 'Фильмы'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(year__gte=1888, year__lte=2100),
                name='ck_movies_year',
            ),
        ]

    def __str__(self):
        return f'{self.title} ({self.year})'


class DiaryEntry(models.Model):
    """Запись в дневнике пользователя: фильм, статус, оценка и отзыв."""

    STATUS_WANT = 'want'
    STATUS_WATCHED = 'watched'
    STATUS_CHOICES = [
        (STATUS_WANT, 'Хочу посмотреть'),
        (STATUS_WATCHED, 'Посмотрел'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='diary_entries',
        verbose_name='Пользователь',
    )
    movie = models.ForeignKey(
        Movie,
        on_delete=models.RESTRICT,
        related_name='diary_entries',
        verbose_name='Фильм',
    )
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default=STATUS_WANT)
    rating = models.PositiveSmallIntegerField('Оценка', null=True, blank=True)
    review = models.TextField('Отзыв', blank=True)
    watched_at = models.DateField('Дата просмотра', null=True, blank=True)
    created_at = models.DateTimeField('Создана', auto_now_add=True)

    class Meta:
        db_table = 'diary_entries'
        ordering = ['-created_at']
        verbose_name = 'Запись дневника'
        verbose_name_plural = 'Записи дневника'
        constraints = [
            models.UniqueConstraint(fields=['user', 'movie'], name='uq_diary_user_movie'),
            models.CheckConstraint(
                condition=models.Q(status__in=['want', 'watched']),
                name='ck_diary_status',
            ),
            models.CheckConstraint(
                condition=models.Q(rating__isnull=True) | models.Q(rating__gte=1, rating__lte=10),
                name='ck_diary_rating',
            ),
        ]

    def __str__(self):
        return f'{self.user} - {self.movie}'


class AiRecommendation(models.Model):
    """История запросов к ИИ: настроение пользователя и ответ нейросети."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_recommendations',
        verbose_name='Пользователь',
    )
    mood = models.CharField('Настроение', max_length=100)
    request_text = models.TextField('Запрос', blank=True)
    response_text = models.TextField('Ответ ИИ')
    created_at = models.DateTimeField('Создана', auto_now_add=True)

    class Meta:
        db_table = 'ai_recommendations'
        ordering = ['-created_at']
        verbose_name = 'Подборка ИИ'
        verbose_name_plural = 'Подборки ИИ'

    def __str__(self):
        return f'{self.user}: {self.mood}'
