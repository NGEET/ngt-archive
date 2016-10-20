from django.apps import AppConfig
from django.db.models.signals import post_migrate


def load_groups(sender, **kwargs):

    from django.contrib.auth.models import Group
    from django.contrib.auth.models import Permission
    add_dataset = Permission.objects.get(codename='add_dataset')
    change_dataset = Permission.objects.get(codename='change_dataset')

    admin = Group.objects.filter(name='NGT Administrator')
    if len(admin) ==0:
        admin = Group.objects.create(name='NGT Administrator')
        admin.permissions.add(add_dataset)
        admin.permissions.add(change_dataset)
        print("{} group created".format(admin.name))
    ngt_user = Group.objects.filter(name='NGT User')
    if len(ngt_user) == 0:
        ngt_user = Group.objects.create(name='NGT User')
        ngt_user.permissions.add(add_dataset)
        ngt_user.permissions.add(change_dataset)
        print("{} group created".format(ngt_user.name))


class ArchiveApiConfig(AppConfig):
    name = 'archive_api'

    def ready(self):
        post_migrate.connect(load_groups, sender=self)


