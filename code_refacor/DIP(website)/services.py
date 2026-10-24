
#Question 1 — Identify and explain the issue
#Component: The blog-notification service in website/services.py.
#Principle: DIP. The notification logic directly used Django’s email function, making the business logic harder to test independently or connect to a different email sender.
#Original relevant logic:

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

def send_blog_notifications(blog_post):
    """Send email notifications to subscribers when a new blog is published"""
    subscribers = BlogSubscription.objects.filter(
        doctor=blog_post.author,
        is_active=True,
        notification_frequency='IMMEDIATE'
    )

    for subscriber in subscribers:
        try:
            subject = f'New Blog Post by Dr. {blog_post.author.get_full_name()}: {blog_post.title}'
            message = f"""
Hello {subscriber.name or 'Reader'},

Dr. {blog_post.author.get_full_name()} has published a new blog post:

Title: {blog_post.title}
Category: {blog_post.get_category_display()}

{blog_post.excerpt}

Read the full post at: {settings.SITE_URL}/blog/{blog_post.slug}/

To unsubscribe from these notifications, please contact us.

Best regards,
Smart Care Hospital Team
            """

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[subscriber.email],
                fail_silently=True
            )

            subscriber.last_notification_sent = timezone.now()
            subscriber.save()

        except Exception as e:
            continue


#The service is tightly coupled to Django’s send_mail. It also suppresses errors and updates last_notification_sent regardless of whether the mail backend sent the message. 
# That makes the behavior harder to test and can leave the database saying a notification was sent when it wasn’t.









#Question 2 — Refactor while preserving behavior
#Proposed improvement: Pass the email sender into the service as a dependency. The service can then be tested using a mock sender, while the application still uses Django’s email function in normal operation. 
# Record the notification as sent only when the sender reports success, and log delivery failures rather than silently ignoring them.
#Refactored relevant logic in website/services.py:

import logging
from collections.abc import Callable
from smtplib import SMTPException

from django.conf import settings
from django.utils import timezone

from website.models import BlogSubscription


logger = logging.getLogger(__name__)


def send_blog_notifications(blog_post, mailer: Callable[..., int]) -> None:
    """Notify immediate subscribers using the supplied email sender."""
    subscribers = BlogSubscription.objects.filter(
        doctor=blog_post.author,
        is_active=True,
        notification_frequency='IMMEDIATE'
    )

    for subscriber in subscribers:
        subject = f'New Blog Post by Dr. {blog_post.author.get_full_name()}: {blog_post.title}'
        message = f"""
Hello {subscriber.name or 'Reader'},

Dr. {blog_post.author.get_full_name()} has published a new blog post:

Title: {blog_post.title}
Category: {blog_post.get_category_display()}

{blog_post.excerpt}

Read the full post at: {settings.SITE_URL}/blog/{blog_post.slug}/

To unsubscribe from these notifications, please contact us.

Best regards,
Smart Care Hospital Team
        """

        try:
            sent_count = mailer(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[subscriber.email],
                fail_silently=False
            )
        except (OSError, SMTPException):
            logger.exception(
                'Failed to send blog notification to %s',
                subscriber.email
            )
            continue

        if sent_count:
            subscriber.last_notification_sent = timezone.now()
            subscriber.save(update_fields=['last_notification_sent'])
        else:
            logger.error(
                'Email sender did not send a blog notification to %s',
                subscriber.email
            )
