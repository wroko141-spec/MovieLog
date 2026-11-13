from django.contrib import admin

from .models import AiRecommendation, DiaryEntry, Genre, Movie


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'created_at')
    list_filter = ('genres', 'year')
    search_fields = ('title',)
    filter_horizontal = ('genres',)


@admin.register(DiaryEntry)
class DiaryEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'status', 'rating', 'watched_at')
    list_filter = ('status',)


@admin.register(AiRecommendation)
class AiRecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'mood', 'created_at')
