import re
from datetime import timedelta

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import PasswordResetToken, User


class AuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ivan', 'ivan@test.ru', 'StrongPass123')

    def test_password_is_hashed(self):
        self.assertNotEqual(self.user.password, 'StrongPass123')
        self.assertTrue(self.user.check_password('StrongPass123'))

    def test_register(self):
        r = self.client.post(reverse('register'), {
            'username': 'petr', 'email': 'petr@test.ru', 'password1': 'Kino2026pass', 'password2': 'Kino2026pass'})
        self.assertRedirects(r, reverse('catalog'))
        self.assertTrue(User.objects.filter(username='petr').exists())

    def test_register_duplicate_email(self):
        r = self.client.post(reverse('register'), {
            'username': 'other', 'email': 'IVAN@test.ru', 'password1': 'Kino2026pass', 'password2': 'Kino2026pass'})
        self.assertContains(r, 'уже зарегистрирован')

    def test_login_by_email(self):
        r = self.client.post(reverse('login'), {'username': 'ivan@test.ru', 'password': 'StrongPass123'})
        self.assertRedirects(r, reverse('diary'))

    def test_admin_role_gets_staff(self):
        admin = User.objects.create_user('boss', 'boss@test.ru', 'StrongPass123', role='admin')
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_admin)


class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ivan', 'ivan@test.ru', 'OldPass12345')

    def get_link_token(self):
        self.client.post(reverse('forgot_password'), {'email': 'ivan@test.ru'})
        self.assertEqual(len(mail.outbox), 1)
        return re.search(r'/accounts/reset/([^/]+)/', mail.outbox[0].body).group(1)

    def test_same_answer_for_unknown_email(self):
        r1 = self.client.post(reverse('forgot_password'), {'email': 'ivan@test.ru'})
        r2 = self.client.post(reverse('forgot_password'), {'email': 'nobody@test.ru'})
        self.assertEqual(r1.content, r2.content)
        self.assertEqual(len(mail.outbox), 1)

    def test_only_hash_is_stored(self):
        token = self.get_link_token()
        saved = PasswordResetToken.objects.get(user=self.user)
        self.assertNotEqual(saved.token_hash, token)
        self.assertEqual(len(saved.token_hash), 64)

    def test_reset_and_token_is_one_time(self):
        token = self.get_link_token()
        url = reverse('reset_password', args=[token])
        r = self.client.post(url, {'new_password1': 'NewPass2026!', 'new_password2': 'NewPass2026!'})
        self.assertRedirects(r, reverse('login'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass2026!'))
        self.assertEqual(self.client.get(url).status_code, 400)

    def test_expired_token(self):
        token = self.get_link_token()
        PasswordResetToken.objects.update(expires_at=timezone.now() - timedelta(minutes=1))
        self.assertEqual(self.client.get(reverse('reset_password', args=[token])).status_code, 400)

    def test_new_request_cancels_old_link(self):
        first = self.get_link_token()
        self.client.post(reverse('forgot_password'), {'email': 'ivan@test.ru'})
        self.assertEqual(self.client.get(reverse('reset_password', args=[first])).status_code, 400)
