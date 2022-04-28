from django.test import TestCase, Client

from ..models import Group, Post, User, Follow


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовый тест',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date='Тестовая дата',
            author=cls.user,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_url_auth(self):
        """Проверка URL- адреса и шаблона для авторизованных пользователей.
        """
        templates_url = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/author/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/comment/': 'posts/post_detail.html',
            '/follow/': 'posts/follow.html',
            f'/profile/{self.user.username}/follow': 'posts/profile.html',
            f'/profile/{self.user.username}/unfollow': 'posts/profile.html',
        }
        for url, template in templates_url.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url, follow=True)
                self.assertTemplateUsed(response, template)

    def test_url_nonauth(self):
        """Проверка редиректа неавторизованных пользователей на
           страницу авторизации.
        """
        templates_url = {
            '/create/': '/auth/login/?next=/create/',
            f'/posts/{self.post.id}/edit/': '/auth/login/?next=/posts/1/edit/',
            f'/posts/{self.post.id}/comment/':
                '/auth/login/?next=/posts/1/comment/',
        }
        for url, template in templates_url.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, template)

    def test_url_author(self):
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_unexisting_page(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')


class FollowURLTests(TestCase):
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
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовый тест',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            # group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
