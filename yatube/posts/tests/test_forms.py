import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsCreateTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            pk=1,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в базе данных."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        last_post = Post.objects.last()
        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post.group, self.group)
        self.assertEqual(last_post.author, self.user)
        self.assertEqual(last_post.image, 'posts/small.gif')

    def test_edit_post(self):
        """При отправке валидной формы редактирования меняется пост в БД."""
        form_data = {
            'text': 'Отредактированный пост',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        edit_post = Post.objects.get(id=self.post.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            edit_post.text, form_data['text']
        )
        self.assertEqual(edit_post.group, self.group)

    def test_non_auth_cannot_create_post(self):
        """Неавторизованный пользователь не может создавать пост"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.pk,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, ('/auth/login/?next=/create/'))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, 200)

    def test_auth_can_create_comment(self):
        """Авторизованный пользователь может создавать коммент"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый коммент',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        last_comment = Comment.objects.last()
        self.assertEqual(last_comment.text, form_data['text'])
        self.assertEqual(last_comment.author, self.user)
        self.assertEqual(last_comment.post, self.post)
        self.assertEqual(response.status_code, 200)

    def test_non_auth_cannot_create_comment(self):
        """Неавторизованный пользователь не может создавать коммент"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый коммент',
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, ('/auth/login/?next=/posts/1/comment/'))
