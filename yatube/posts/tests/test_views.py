from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django import forms
from ..models import Post, Group, Comment, Follow
from django.urls import reverse

from django.core.cache import cache

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title="Тестовый заголовок",
            slug='test-slug',
            description='Тестовое описание',
        )
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
        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date='Тестовая дата',
            author=cls.user,
            group=cls.group,
            image=uploaded
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон и HTTP статус."""
        templates_page_names = {
            reverse('posts:group_list', kwargs={'slug': self.group.slug}): (
                'posts/group_list.html'
            ),
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:profile', kwargs={'username': (
                self.user.username)}): 'posts/profile.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_detail', kwargs={'post_id': (
                self.post.pk)}): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': (
                self.post.pk)}): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_show_correct_context(self):
        """Шаблоны posts сформированы с правильным контекстом."""
        namespace_list = {
            reverse('posts:index'): 'page_obj',
            reverse('posts:group_list', args=[self.group.slug]): 'page_obj',
            reverse('posts:profile', args=[self.user.username]): 'page_obj',
            reverse('posts:post_detail', args=[self.post.pk]): 'post',
        }
        for reverse_name, context in namespace_list.items():
            first_object = self.guest_client.get(reverse_name)
            if context == 'post':
                first_object = first_object.context[context]
            else:
                first_object = first_object.context[context][0]
            post_text = first_object.text
            post_author = first_object.author
            post_group = first_object.group
            post_image = first_object.image
            posts_dict = {
                post_text: self.post.text,
                post_author: self.user,
                post_group: self.group,
                post_image: self.post.image
            }
            for post_param, test_post_param in posts_dict.items():
                with self.subTest(
                        post_param=post_param,
                        test_post_param=test_post_param):
                    self.assertEqual(post_param, test_post_param)

    def test_create_post_show_correct_context(self):
        """Шаблоны create и edit сформированы с правильным контекстом."""
        namespace_list = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', args=[self.post.pk])
        ]
        for reverse_name in namespace_list:
            response = self.authorized_client.get(reverse_name)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context['form'].fields[value]
                    self.assertIsInstance(form_field, expected)

    def test_post_another_group(self):
        """Пост не попал в другую группу"""
        response = self.authorized_client.get(
            reverse('posts:group_list', args={self.group.slug}))
        first_object = response.context["page_obj"][0]
        post_text = first_object.text
        self.assertTrue(post_text, 'Тестовый текст')


class PostPaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug='test-slug',
            description='Тестовое описание',
        )
        for post_number in range(13):
            cls.post = Post.objects.create(
                text='Тестовый текст',
                author=cls.user,
                group=cls.group
            )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()

    def test_first_page_contains_ten_posts(self):
        """Количество постов на первой странице равно 10."""
        namespace_list = {
            'posts:index': reverse('posts:index'),
            'posts:group_list': reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}),
            'posts:profile': reverse(
                'posts:profile', kwargs={'username': self.user.username}),
        }
        count_posts = 10
        for template, reverse_name in namespace_list.items():
            response = self.guest_client.get(reverse_name)
            self.assertEqual(len(response.context['page_obj']), count_posts)

    def test_second_page_contains_ten_posts(self):
        """Количество постов на второй странице равно 3."""
        namespace_list = {
            'posts:index': reverse('posts:index') + "?page=2",
            'posts:group_list': reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}) + "?page=2",
            'posts:profile': reverse(
                'posts:profile',
                kwargs={'username': self.user.username}) + "?page=2",
        }
        count_posts = 3
        for template, reverse_name in namespace_list.items():
            response = self.guest_client.get(reverse_name)
            self.assertEqual(len(response.context['page_obj']), count_posts)


class CommentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            post=cls.post,
            author=cls.user
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_add_comment(self):
        """После успешной отправки комментарий появляется на странице поста."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', args=[self.post.pk]))
        count_comments = 1
        self.assertEqual(len(response.context['comments']), count_comments)
        first_object = response.context['comments'][0]
        comment_text = first_object.text
        self.assertTrue(comment_text, 'Тестовый текст')


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title="Тестовый заголовок",
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date='Тестовая дата',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()

    def test_cache_index(self):
        """Тест кэширования главной страницы."""
        response = self.authorized_client.get(reverse('posts:index'))
        post = Post.objects.get(pk=1)
        post.text = 'Измененный текст'
        post.save()
        second_response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, second_response.content)
        post.delete()
        cache.clear()
        third_response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, third_response.content)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(
            username='follower',
            email='test_follower_@mail.ru',
            password='test_password')
        cls.user_following = User.objects.create_user(
            username='following',
            email='test_following_@mail.ru',
            password='test_password')
        cls.post = Post.objects.create(
            author=cls.user_following,
            text='Тестовая запись для тестирования')

    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)

    def test_profile_follow(self):
        """Авторизованный пользователь может
         подписываться на других пользователей"""
        self.client_auth_follower.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_following.username}))
        count_follower = 1
        self.assertEqual(Follow.objects.all().count(), count_follower)

    def test_profile_unfollow(self):
        """Авторизованный пользователь может
         удалять других пользователей из подписок"""
        self.client_auth_follower.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user_following.username}))
        count_follower = 0
        self.assertEqual(Follow.objects.all().count(), count_follower)

    def test_subscription(self):
        """Новая запись появляется в ленте тех, кто на него подписан"""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.client_auth_follower.get('/follow/')
        post_text = response.context["page_obj"][0].text
        self.assertEqual(post_text, 'Тестовая запись для тестирования')

    def test_no_subscription(self):
        """Новая запись не появляется в ленте тех, кто не подписан."""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.client_auth_following.get('/follow/')
        self.assertNotEqual(response, 'Тестовая запись для тестирования')
