from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import api, views

router = DefaultRouter(trailing_slash=True)
router.include_root_view = False
router.register('movies', api.MovieViewSet, basename='api-movies')
router.register('genres', api.GenreViewSet, basename='api-genres')
router.register('diary', api.DiaryEntryViewSet, basename='api-diary')

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog/', views.catalog, name='catalog'),
    path('movie/<int:pk>/', views.movie_detail, name='movie'),
    path('diary/', views.my_diary, name='diary'),
    path('ai/', views.ai_page, name='ai'),
    path('api/', api.api_root, name='api-root'),
    path('api/stats/', api.stats, name='api-stats'),
    path('api/recommendations/', api.RecommendationListView.as_view(), name='api-recommendations'),
    path('api/recommendations/new/', api.CreateRecommendationView.as_view(), name='api-recommend'),
    path('api/', include(router.urls)),
]
