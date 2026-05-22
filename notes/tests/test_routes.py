from http import HTTPStatus

from django.test import Client
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_not_author = User.objects.create(username='user1')
        cls.client_author = User.objects.create(username='user2')
        cls.notes = Note.objects.create(
            title='Заголовокэ',
            text='Text',
            author=cls.client_author,
            slug='slug')
        cls.client_author = cls._create_client_author(cls.client_author)
        cls.client_not_author = cls._create_client_author(
            cls.client_not_author)

    @classmethod
    def _create_client_author(cls, user):
        user_client = Client()
        user_client.force_login(user)
        return user_client

    def test_pages_availability_for_client(self):
        url_status = [
            (self.client_not_author, 'notes:list',
             HTTPStatus.OK, None, 'get'),
            (self.client_not_author, 'notes:add',
             HTTPStatus.OK, None, 'get'),
            (self.client_not_author, 'notes:success',
             HTTPStatus.OK, None, 'get'),
            (self.client_not_author, 'notes:detail',
             HTTPStatus.NOT_FOUND, (self.notes.slug, ), 'get'),
            (self.client_not_author, 'notes:edit', HTTPStatus.NOT_FOUND,
             (self.notes.slug, ), 'get'),
            (self.client_not_author, 'notes:delete',
             HTTPStatus.NOT_FOUND, (self.notes.slug, ), 'get'),
            (self.client_author, 'notes:detail', HTTPStatus.OK,
             (self.notes.slug, ), 'get'),
            (self.client_author, 'notes:edit', HTTPStatus.OK,
             (self.notes.slug, ), 'get'),
            (self.client_author, 'notes:delete', HTTPStatus.OK,
             (self.notes.slug, ), 'get'),
            (self.client, 'notes:home', HTTPStatus.OK, None, 'get'),
            (self.client, 'users:login', HTTPStatus.OK, None, 'get'),
            (self.client, 'users:signup', HTTPStatus.OK, None, 'get'),
            (self.client, 'users:logout', HTTPStatus.OK, None, 'post'),
        ]
        for user, name, status, args, method in url_status:
            with self.subTest(name=name, args=args):
                url = reverse(name, args=args)
                http_method = getattr(user, method)
                response = http_method(url)
                self.assertEqual(response.status_code, status)

    def test_redirect_for_another_user(self):
        urls_status = [
            ('notes:list', None),
            ('notes:success', None),
            ('notes:add', None),
            ('notes:detail', (self.notes.slug, )),
            ('notes:edit', (self.notes.slug, )),
            ('notes:delete', (self.notes.slug, )),
        ]
        for name, args in urls_status:
            with self.subTest(name=name, args=args):
                url = reverse(name, args=args)
                login_url = f'{reverse('users:login')}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, login_url)
