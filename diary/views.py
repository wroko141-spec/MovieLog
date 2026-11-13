from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .api import user_stats
from .models import AiRecommendation, DiaryEntry, Genre, Movie


def home(request):
    latest = Movie.objects.prefetch_related('genres').order_by('-created_at')[:6]
    return render(request, 'diary/home.html', {'latest': latest, 'movies_count': Movie.objects.count()})


def catalog(request):
    q = request.GET.get('q', '').strip()[:100]
    genre_id = request.GET.get('genre', '')
    movies = Movie.objects.prefetch_related('genres')
    if q:
        movies = movies.filter(title__icontains=q)
    if genre_id.isdigit():
        movies = movies.filter(genres__id=int(genre_id))
    page = Paginator(movies.distinct(), 12).get_page(request.GET.get('page'))
    in_diary = {}
    if request.user.is_authenticated:
        in_diary = dict(DiaryEntry.objects.filter(user=request.user).values_list('movie_id', 'status'))
    return render(request, 'diary/catalog.html', {
        'page': page, 'q': q, 'genres': Genre.objects.all(),
        'genre_id': int(genre_id) if genre_id.isdigit() else None, 'in_diary': in_diary,
    })


def movie_detail(request, pk):
    movie = get_object_or_404(Movie.objects.prefetch_related('genres'), pk=pk)
    entry = None
    if request.user.is_authenticated:
        entry = DiaryEntry.objects.filter(user=request.user, movie=movie).first()
    reviews = (DiaryEntry.objects.filter(movie=movie, status='watched').exclude(review='')
               .select_related('user').order_by('-created_at')[:10])
    return render(request, 'diary/movie.html', {'movie': movie, 'entry': entry, 'reviews': reviews, 'ratings': range(1, 11)})


@login_required
def my_diary(request):
    status = request.GET.get('status', '')
    entries = DiaryEntry.objects.filter(user=request.user).select_related('movie').prefetch_related('movie__genres')
    if status in ('want', 'watched'):
        entries = entries.filter(status=status)
    return render(request, 'diary/diary.html', {'entries': entries, 'status': status, 'stats': user_stats(request.user)})


@login_required
def ai_page(request):
    history = AiRecommendation.objects.filter(user=request.user)[:5]
    return render(request, 'diary/ai.html', {'history': history})


def page_not_found(request, exception=None):
    return render(request, '404.html', status=404)
