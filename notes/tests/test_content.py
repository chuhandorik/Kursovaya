from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestCreateNotes(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='user1')
        cls.notauthor = User.objects.create(username='user2')
        cls.news = Note.objects.create(
            title="title",
            text="TEXT",
            slug="text_slug",
            author=cls.author
        )
        cls.list_urls = (
            ('notes:add', None),
            ('notes:edit', (cls.news.slug, )))

    def test_note_in_list_page(self):
        self.client.force_login(self.author)
        url = reverse('notes:list')
        response = self.client.get(url)
        self.assertIn(self.news, response.context['object_list'])

    def test_notes_list_for_different_users(self):
        self.client.force_login(self.notauthor)
        url = reverse('notes:list')
        response = self.client.get(url)
        self.assertNotIn(self.news, response.context['object_list'])

    def test_pages_contains_form(self):
        self.client.force_login(self.author)
        for name, args in self.list_urls:
            url = reverse(name, args=args)
            response = self.client.post(url)
            self.assertIn('form', response.context)
            self.assertIsInstance(response.context['form'], NoteForm)
