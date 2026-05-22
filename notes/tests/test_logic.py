from http import HTTPStatus

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from pytils.translit import slugify

from notes.models import Note
from notes.forms import WARNING

User = get_user_model()


class TestNoteCreate(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('notes:add')
        cls.author = User.objects.create(username='user1')
        cls.notauthor = User.objects.create(username='user2')
        cls.note = Note.objects.create(
            title="title",
            text="TEXT",
            slug="text_slug",
            author=cls.author
        )
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug'
        }

    def test_user_can_create_note(self):
        Note.objects.all().delete()
        self.client.force_login(self.author)
        self.client.post(self.url, self.form_data)
        new_news = Note.objects.get()
        self.assertEqual(new_news.title, self.form_data['title'])
        self.assertEqual(new_news.text, self.form_data['text'])
        self.assertEqual(new_news.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        note_count = Note.objects.count()
        response = self.client.post(self.url, self.form_data)
        new_url = f'{reverse('users:login')}?next={self.url}'
        self.assertEqual(Note.objects.count(), note_count)
        self.assertRedirects(response, new_url)

    def test_not_unique_slug(self):
        note_count = Note.objects.count()
        self.client.force_login(self.author)
        self.form_data['slug'] = self.note.slug
        response = self.client.post(self.url, self.form_data)
        self.assertFormError(
            response.context['form'],
            'slug',
            self.form_data['slug'] + WARNING)
        self.assertEqual(Note.objects.count(), note_count)

    def test_empty_slug(self):
        Note.objects.all().delete()
        self.form_data.pop('slug')
        self.client.force_login(self.author)
        self.client.post(self.url, self.form_data)
        self.assertEqual(Note.objects.count(), 1)
        notes = Note.objects.get()
        max_lenght_for_slug = Note._meta.get_field('slug').max_length
        self.assertEqual(
            notes.slug,
            slugify(notes.title)[:max_lenght_for_slug])

    def test_author_can_edit_note(self):
        url = reverse('notes:edit', args=(self.note.slug,))
        self.client.force_login(self.author)
        response = self.client.post(url, self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        note = Note.objects.get(id=self.note.id)
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])
        self.assertEqual(note.author, self.author)

    def test_other_user_cant_edit_note(self):
        url = reverse('notes:edit', args=(self.note.slug,))
        self.client.force_login(self.notauthor)
        response = self.client.post(url, self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)
        self.assertEqual(self.note.author, note_from_db.author)

    def test_author_can_delete_note(self):
        note_id = self.note.id
        url = reverse('notes:delete', args=(self.note.slug, ))
        self.client.force_login(self.author)
        response = self.client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertFalse(Note.objects.filter(id=note_id).exists())

    def test_other_user_cant_delete_note(self):
        note_id = self.note.id
        url = reverse('notes:delete', args=(self.note.slug, ))
        self.client.force_login(self.notauthor)
        response = self.client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTrue(Note.objects.filter(id=note_id).exists())
