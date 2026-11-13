from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User

from .models import AiRecommendation, DiaryEntry, Genre, Movie


class ApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ivan', 'ivan@test.ru', 'StrongPass123')
        self.other = User.objects.create_user('petr', 'petr@test.ru', 'StrongPass123')
        self.admin = User.objects.create_user('boss', 'boss@test.ru', 'StrongPass123', role='admin')
        self.comedy = Genre.objects.create(name='Комедия')
        self.drama = Genre.objects.create(name='Драма')
        self.m1 = Movie.objects.create(title='Один дома', year=1990)
        self.m1.genres.add(self.comedy)
        self.m2 = Movie.objects.create(title='Зелёная миля', year=1999)
        self.m2.genres.add(self.drama)
        self.api = APIClient()

    def test_catalog_is_public_and_search_works(self):
        r = self.api.get('/api/movies/?q=дома')
        self.assertEqual(r.status_code, 200)
        self.assertEqual([m['title'] for m in r.data['results']], ['Один дома'])

    def test_only_admin_can_add_movie(self):
        self.api.force_authenticate(self.user)
        self.assertEqual(self.api.post('/api/movies/', {'title': 'X', 'year': 2000}).status_code, 403)
        self.api.force_authenticate(self.admin)
        self.assertEqual(self.api.post('/api/movies/', {'title': 'X', 'year': 2000}).status_code, 201)

    def test_diary_requires_login(self):
        self.assertEqual(self.api.get('/api/diary/').status_code, 403)

    def test_add_and_rate(self):
        self.api.force_authenticate(self.user)
        r = self.api.post('/api/diary/', {'movie_id': self.m1.id, 'status': 'watched', 'rating': 9, 'review': 'Классика'}, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(DiaryEntry.objects.get().rating, 9)

    def test_rating_validation(self):
        self.api.force_authenticate(self.user)
        r = self.api.post('/api/diary/', {'movie_id': self.m1.id, 'status': 'watched', 'rating': 15}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_no_duplicates(self):
        self.api.force_authenticate(self.user)
        self.api.post('/api/diary/', {'movie_id': self.m1.id, 'status': 'want'}, format='json')
        r = self.api.post('/api/diary/', {'movie_id': self.m1.id, 'status': 'want'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_cannot_touch_foreign_entry(self):
        entry = DiaryEntry.objects.create(user=self.other, movie=self.m1)
        self.api.force_authenticate(self.user)
        self.assertEqual(self.api.delete(f'/api/diary/{entry.id}/').status_code, 404)
        self.assertTrue(DiaryEntry.objects.filter(id=entry.id).exists())

    def test_csrf_is_required_for_session_api(self):
        client = APIClient(enforce_csrf_checks=True)
        client.login(username='ivan', password='StrongPass123')
        r = client.post('/api/diary/', {'movie_id': self.m1.id, 'status': 'want'}, format='json')
        self.assertEqual(r.status_code, 403)

    def test_ai_recommendation_by_mood(self):
        DiaryEntry.objects.create(user=self.user, movie=self.m2, status='watched', rating=10)
        self.api.force_authenticate(self.user)
        r = self.api.post('/api/recommendations/new/', {'mood': 'хочу посмеяться'}, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertIn('Один дома', r.data['response_text'])
        self.assertNotIn('Зелёная миля', r.data['response_text'])  # уже посмотрел
        self.assertEqual(AiRecommendation.objects.count(), 1)

    def test_stats(self):
        DiaryEntry.objects.create(user=self.user, movie=self.m1, status='watched', rating=8)
        DiaryEntry.objects.create(user=self.user, movie=self.m2, status='want')
        self.api.force_authenticate(self.user)
        r = self.api.get('/api/stats/')
        self.assertEqual((r.data['watched'], r.data['want'], r.data['avg_rating']), (1, 1, 8.0))


class PagesTests(TestCase):
    def test_pages_open(self):
        Movie.objects.create(title='Тест', year=2000)
        for name in ('home', 'catalog', 'login', 'register', 'forgot_password'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

    def test_xss_is_escaped(self):
        m = Movie.objects.create(title='<script>alert(1)</script>', year=2000)
        r = self.client.get(reverse('movie', args=[m.id]))
        self.assertNotContains(r, '<script>alert(1)</script>')
        self.assertContains(r, '&lt;script&gt;')

    def test_diary_needs_login(self):
        self.assertRedirects(self.client.get(reverse('diary')), reverse('login') + '?next=/diary/')

    def test_404(self):
        self.assertEqual(self.client.get('/nope/').status_code, 404)
