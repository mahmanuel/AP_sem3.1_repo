from users.models import User
from website.models import Blog, BlogSubscription
from website.services import send_blog_notifications


class BlogNotificationTests(TestCase):
    def setUp(self):
        self.doctor = User.objects.create_user(
            username='blog-doctor',
            email='doctor@example.com',
            first_name='Ada',
            last_name='Lovelace',
            role=User.DOCTOR
        )
        self.blog_post = Blog.objects.create(
            title='Healthy Living',
            author=self.doctor,
            content='Article content',
            excerpt='A short summary',
            status='PUBLISHED'
        )
        self.subscription = BlogSubscription.objects.create(
            email='reader@example.com',
            doctor=self.doctor
        )

    def test_sends_notification_and_records_success(self):
        mailer = Mock(return_value=1)

        send_blog_notifications(self.blog_post, mailer)

        self.subscription.refresh_from_db()
        self.assertIsNotNone(self.subscription.last_notification_sent)
        mailer.assert_called_once()
        self.assertEqual(
            mailer.call_args.kwargs['recipient_list'],
            ['reader@example.com']
        )
        self.assertIn(
            f'/blog/{self.blog_post.slug}/',
            mailer.call_args.kwargs['message']
        )

    def test_failed_delivery_is_logged_and_not_marked_as_sent(self):
        second_subscription = BlogSubscription.objects.create(
            email='another-reader@example.com',
            doctor=self.doctor
        )
        mailer = Mock(side_effect=[SMTPException('mail server unavailable'), 1])

        with self.assertLogs('website.services', level='ERROR'):
            send_blog_notifications(self.blog_post, mailer)

        self.subscription.refresh_from_db()
        second_subscription.refresh_from_db()
        self.assertEqual(mailer.call_count, 2)
        self.assertEqual(
            sum(
                subscription.last_notification_sent is not None
                for subscription in (self.subscription, second_subscription)
            ),
            1
        )