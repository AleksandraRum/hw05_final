import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.core.cache import cache
from django.urls import reverse
from django import forms

from ..models import Post, Group, User, Follow
from ..views import NUM_OF_P

COUNT_POSTS = 13

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
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
            content_type='image/gif',
        )
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}):
                'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_correct_context_index(self):
        """Проверяем, что index-шаблон сформирвоан с правилным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context, 'Объекта нет')
        first_obj = response.context['page_obj'][0]
        self.assertEqual(first_obj, self.post)
        self.assertEqual(first_obj.image, self.post.image)

    def test_correct_context_group_list(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}))
        self.assertIn('group', response.context, 'Объекта нет')
        group_field = response.context['group']
        first_obj = response.context['page_obj'][0]
        self.assertEqual(group_field, self.group)
        self.assertEqual(first_obj, self.post)
        self.assertEqual(first_obj.image, self.post.image)

    def test_correct_context_profile(self):
        """Проверяем, что profile-шаблон сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        first_obj = response.context['page_obj'][0]
        self.assertEqual(first_obj, self.post)
        self.assertEqual(first_obj.author, self.post.author)
        self.assertEqual(
            first_obj.author.posts.all().count(), 1
        )
        self.assertEqual(first_obj.image, self.post.image)

    def test_correct_context_post_detail(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}))
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').author, self.post.author)
        self.assertEqual(
            response.context.get('post').author.posts.all().count(), 1
        )
        self.assertEqual(response.context.get('post').image, self.post.image)

    def test_correct_context_create_post(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_correct_context_edit_post(self):
        """Проверяем, что шаблон post_create редактирует пост с верным id"""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_without_group(self):
        Post.objects.create(
            author=self.user,
            text='Тестовый пост без группы',
        )
        # Проверяем, что пост попал на главную страницу
        response = self.authorized_client.get(reverse('posts:index'))
        first_obj = response.context['page_obj'][0]
        text_0_index = first_obj.text
        self.assertEqual(text_0_index, 'Тестовый пост без группы')
        # Проверяем, что пост не попал в группу
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}))
        first_obj = response.context['page_obj'][0]
        text_0_group = first_obj.text
        self.assertNotEqual(text_0_group, 'Тестовый пост без группы')
        # Проверяем, что пост в профайле пользователя
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        first_obj = response.context['page_obj'][0]
        text_0_group = first_obj.text
        self.assertEqual(text_0_index, 'Тестовый пост без группы')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug',
        )
        for i in range(COUNT_POSTS):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'{i} тестовый текст',
                group=cls.group,
            )

    def test_index_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context['page_obj']), NUM_OF_P)

    def test_index_second_page_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']), COUNT_POSTS - NUM_OF_P
        )

    def test_post_list_first_page_contains_ten_records(self):
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test-slug'}
        ))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context['page_obj']), NUM_OF_P)

    def test_post_list_second_page_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test-slug'}) + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj']), COUNT_POSTS - NUM_OF_P
        )

    def test_profile_first_page_contains_ten_records(self):
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username}
        ))
        self.assertEqual(len(response.context['page_obj']), NUM_OF_P)

    def test_profile_second_page_contains_ten_records(self):
        response = self.client.get(reverse(
            'posts:profile', kwargs={
                'username': self.user.username
            }) + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj']), COUNT_POSTS - NUM_OF_P
        )


class CashViewTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='author')
        cls.post_cash = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cash_page(self):
        """Проверяем кэш на главной странице."""
        response = self.authorized_client.get(reverse('posts:index')).content
        post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
        )
        post.delete()
        self.assertEqual(
            response, self.authorized_client.get(
                reverse('posts:index')).content
        )
        cache.clear()
        self.assertNotEqual(
            response, self.authorized_client.get(
                reverse('posts:index')).content
        )

# class ViewTestClass(TestCase):
    def test_error_page(self):
        response = self.client.get('/nonexist-page/')
        # Проверьте, что статус ответа сервера - 404
        # Проверьте, что используется шаблон core/404.html
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')


class FollowPagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='noname')
        cls.follower = User.objects.create_user(username='follower')
        cls.author = User.objects.create_user(username='following')
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.author,
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def authorized_can_follow(self):
        """Авторизованный пользователь может подписываться на других
    пользователей."""
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author}))
        self.assertTrue(Follow.objects.filter(
            user=self.authorized_client,
            author=self.author).exists())

    def authorized_can_unfollow(self):
        """Авторизованный пользователь может отписаться от автора"""
        object = Follow.objects.create(user=self.user, author=self.author)
        Follower_before = self.user.follower.filter(author=self.author).count()
        object.delete()
        Follower_after = self.user.follower.filter(author=self.author).count()
        self.assertEqual(Follower_before, Follower_after - 1)

    def post_in_follow(self):
        Follow.objects.create(user=self.user, author=self.author)
        post = Post.objects.create(
            text="Новый пост",
            author=self.author,
        )
        response = (self.authorized_client.get(reverse('posts:follow_index')))
        self.assertIn(
            post.text, response.context
        )
