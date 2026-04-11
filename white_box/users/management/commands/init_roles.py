from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Initialize default roles (groups) and permissions.'

    def handle(self, *args, **options): 
        user_group, _ = Group.objects.get_or_create(name='user')
        moderator_group, _ = Group.objects.get_or_create(name='moderator')
        admin_group, _ = Group.objects.get_or_create(name='admin')

        user_perms = Permission.objects.filter( 
            content_type__app_label='posts', #content_type__app_label='posts'表示只获取与posts应用相关的权限
            codename__in=['add_postcontent', 'add_review', 'add_report', 'view_postcontent', 'view_review'], #codename__in=['add_postcontent', 'add_review', 'add_report', 'view_postcontent', 'view_review']表示只获取这些特定权限的权限对象
        )
        user_group.permissions.set(user_perms)

        moderator_perms = Permission.objects.filter(
            content_type__app_label='posts',
            codename__in=[
                'view_postcontent',
                'view_review',
                'view_report',
                'change_review',
                'delete_review',
                'change_postcontent',
                'delete_postcontent',
                'change_report',
            ],
        )
        moderator_group.permissions.set(moderator_perms)

        admin_perms = Permission.objects.filter(content_type__app_label='posts')
        admin_group.permissions.set(admin_perms)

        self.stdout.write(self.style.SUCCESS('Roles initialized: user, moderator, admin'))
