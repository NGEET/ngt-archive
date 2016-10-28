from django.apps import AppConfig
from django.db.models.signals import post_migrate


def load_groups(sender, **kwargs):
    from django.contrib.auth.models import Group
    from django.contrib.auth.models import Permission
    add_dataset = Permission.objects.get(codename='add_dataset')
    add_site = Permission.objects.get(codename='add_site')
    add_plot = Permission.objects.get(codename='add_plot')
    add_measurementvariable = Permission.objects.get(codename='add_measurementvariable')
    add_contact = Permission.objects.get(codename='add_person')
    change_dataset = Permission.objects.get(codename='change_dataset')
    change_site = Permission.objects.get(codename='change_site')
    change_plot = Permission.objects.get(codename='change_plot')
    change_contact = Permission.objects.get(codename='change_person')
    change_measurementvariable = Permission.objects.get(codename='change_measurementvariable')
    can_approve_submitted = Permission.objects.get(codename='approve_submitted_dataset')
    can_unsubmit_submitted = Permission.objects.get(codename='unsubmit_submitted_dataset')
    can_edit_draft = Permission.objects.get(codename='edit_draft_dataset')

    admin = Group.objects.filter(name='NGT Administrator')
    if len(admin) == 0:
        admin = Group.objects.create(name='NGT Administrator')
        for perm in [add_measurementvariable, change_measurementvariable, change_dataset, add_dataset, add_site,
                     add_plot, add_contact, change_site, change_plot, change_contact, can_approve_submitted,
                     can_unsubmit_submitted,
                     can_edit_draft]:
            admin.permissions.add(perm)
        admin.save()
        print("{} group created".format(admin.name))
    ngt_user = Group.objects.filter(name='NGT User')
    if len(ngt_user) == 0:
        ngt_user = Group.objects.create(name='NGT User')
        for perm in [change_dataset, add_dataset, add_contact, can_edit_draft]:
            ngt_user.permissions.add(perm)
        ngt_user.save()
        print("{} group created".format(ngt_user.name))


class ArchiveApiConfig(AppConfig):
    name = 'archive_api'

    def ready(self):
        post_migrate.connect(load_groups, sender=self)
