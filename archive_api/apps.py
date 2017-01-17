from django.apps import AppConfig
from django.db.models.signals import post_migrate


def load_groups(sender, **kwargs):
    import archive_api.models
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
    can_unapprove_submitted = Permission.objects.get(codename='unapprove_approved_dataset')
    can_edit_draft = Permission.objects.get(codename='edit_draft_dataset')
    can_delete_draft = Permission.objects.get(codename='delete_draft_dataset')
    can_delete_submitted = Permission.objects.get(codename='delete_submitted_dataset')
    can_view_all_datasets = Permission.objects.get(codename='view_all_datasets')
    can_view_ngeet_approved_datasets = Permission.objects.get(codename='view_ngeet_approved_datasets')

    admin = Group.objects.filter(name='NGT Administrator')
    if len(admin) == 0:
        admin = Group.objects.create(name='NGT Administrator')
        for perm in [add_measurementvariable, change_measurementvariable, change_dataset, add_dataset, add_site,
                     add_plot, add_contact, change_site, change_plot, change_contact, can_approve_submitted,
                     can_unsubmit_submitted, can_unapprove_submitted, can_delete_draft, can_delete_submitted,
                     can_edit_draft, can_view_all_datasets]:
            admin.permissions.add(perm)
        admin.save()
        print("{} group created".format(admin.name))

    for id, name in archive_api.models.PERSON_ROLE_CHOICES:
        ngt_user = Group.objects.filter(name='NGT {}'.format(name))
        if len(ngt_user) == 0:
            ngt_user = Group.objects.create(name='NGT {}'.format(name))
            for perm in [change_dataset, add_dataset, add_contact, can_edit_draft, can_delete_draft,
                         can_view_ngeet_approved_datasets]:
                ngt_user.permissions.add(perm)
            ngt_user.save()
            print("{} group created".format(ngt_user.name))


class ArchiveApiConfig(AppConfig):
    name = 'archive_api'

    def ready(self):
        post_migrate.connect(load_groups, sender=self)
        import archive_api.signals
