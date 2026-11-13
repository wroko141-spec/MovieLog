from django.db.models import Avg, Count, Q
from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import AiRecommendation, DiaryEntry, Genre, Movie
from .permissions import IsAdminOrReadOnly
from .serializers import (AiRecommendationSerializer, AiRequestSerializer, DiaryEntrySerializer,
                          GenreSerializer, MovieSerializer)
from .services import AiService


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None


class MovieViewSet(viewsets.ModelViewSet):
    serializer_class = MovieSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = Movie.objects.prefetch_related('genres')
        q = self.request.query_params.get('q', '').strip()
        genre = self.request.query_params.get('genre')
        if q:
            qs = qs.filter(title__icontains=q)
        if genre and genre.isdigit():
            qs = qs.filter(genres__id=int(genre))
        return qs.distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class DiaryEntryViewSet(viewsets.ModelViewSet):
    serializer_class = DiaryEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # пользователь видит и меняет только свои записи
        qs = DiaryEntry.objects.filter(user=self.request.user).select_related('movie').prefetch_related('movie__genres')
        st = self.request.query_params.get('status')
        if st in (DiaryEntry.STATUS_WANT, DiaryEntry.STATUS_WATCHED):
            qs = qs.filter(status=st)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RecommendationListView(generics.ListAPIView):
    serializer_class = AiRecommendationSerializer

    def get_queryset(self):
        return AiRecommendation.objects.filter(user=self.request.user)


class CreateRecommendationView(APIView):
    """POST /api/recommendations/new/ - подбор фильмов по настроению (не чаще 10 раз в минуту)."""
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'ai'

    def post(self, request):
        data = AiRequestSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        rec = AiService().recommend(request.user, data.validated_data['mood'])
        return Response(AiRecommendationSerializer(rec).data, status=status.HTTP_201_CREATED)


def user_stats(user):
    entries = DiaryEntry.objects.filter(user=user)
    agg = entries.aggregate(
        total=Count('id'),
        watched=Count('id', filter=Q(status=DiaryEntry.STATUS_WATCHED)),
        want=Count('id', filter=Q(status=DiaryEntry.STATUS_WANT)),
        avg=Avg('rating'),
    )
    top = (Genre.objects.filter(movies__diary_entries__user=user, movies__diary_entries__status='watched')
           .annotate(n=Count('id')).order_by('-n', 'name')[:3])
    return {
        'total': agg['total'],
        'watched': agg['watched'],
        'want': agg['want'],
        'avg_rating': round(agg['avg'], 1) if agg['avg'] else None,
        'top_genres': [{'name': g.name, 'count': g.n} for g in top],
    }


@api_view(['GET'])
def stats(request):
    return Response(user_stats(request.user))


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    return Response({
        'movies': '/api/movies/', 'genres': '/api/genres/', 'diary': '/api/diary/',
        'recommendations': '/api/recommendations/', 'recommend': '/api/recommendations/new/', 'stats': '/api/stats/',
    })
