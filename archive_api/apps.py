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
    can_edit_own = Permission.objects.get(codename='edit_own_dataset')
    can_edit_all = Permission.objects.get(codename='edit_all_dataset')
    can_view_all_datasets = Permission.objects.get(codename='view_all_datasets')
    can_view_ngeet_approved_datasets = Permission.objects.get(codename='view_ngeet_approved_datasets')
    can_upload_large_file = Permission.objects.get(codename='upload_large_file_dataset')

    admin = Group.objects.filter(name='NGT Administrator')
    if len(admin) == 0:
        admin = Group.objects.create(name='NGT Administrator')
        print("{} group created".format(admin.name))
    else:
        admin = admin[0]

    admin.permissions.clear()
    admin.permissions.add(add_measurementvariable, change_measurementvariable, change_dataset, add_dataset, add_site,
                 add_plot, add_contact, change_site, change_plot, change_contact, can_approve_submitted,
                 can_edit_own, can_edit_all, can_view_all_datasets,
                 can_upload_large_file)
    admin.save()
    print("{} group permissions updated".format(admin.name))

    for id, name in archive_api.models.PERSON_ROLE_CHOICES:
        ngt_group = Group.objects.filter(name='NGT {}'.format(name))
        if len(ngt_group) == 0:
            ngt_group = Group.objects.create(name='NGT {}'.format(name))
            print("{} group created".format(ngt_group))
        else:
            ngt_group = ngt_group[0]
        ngt_group.permissions.clear()
        ngt_group.permissions.add(change_dataset, add_dataset, add_contact, can_edit_own,
                         can_view_ngeet_approved_datasets)
        ngt_group.save()
        print("{} group permissions updated".format(ngt_group))


class ArchiveApiConfig(AppConfig):
    name = 'archive_api'
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        post_migrate.connect(load_groups, sender=self)
        import archive_api.signals
