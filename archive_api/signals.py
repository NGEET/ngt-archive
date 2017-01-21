import django_auth_ldap.backend
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.signals import user_logged_in
from django.core.mail import EmailMessage
from django.dispatch import Signal

import archive_api
from archive_api import permissions
from archive_api.models import DataSet, Person

# Signal for Dataset Status changes
dataset_status_change = Signal(providing_args=['request', 'user', 'instance', 'original_status'])


def get_setting(setting_name):
    """
    Get the settings value if it exists
    :param setting_name:
    :return:
    """
    if hasattr(settings,setting_name):
        return getattr(settings,setting_name,'')


def notify_admin_to_activate_user(sender, user, **kwargs):
    """
    After the user is authenticated check to see if they have any groups. If they do
    not, look them up in the Person table.  If they exist, add them to the 'NGT Team' or 'NGT Collaborator' group.

    The Person must have a role of Collaborator or Team

    :param sender:
    :param user:
    :param kwargs:
    :return:
    """

    if not user.groups.all():
        # check existing list
        # if not in any of these groups send email to admins

        person = None
        try:
            person = Person.objects.get(email=user.email, initial_role__lt=2)  # Person is a collaborator or team
        except Person.DoesNotExist:

            people = Person.objects.all().filter(first_name__iexact=user.first_name, last_name__iexact=user.last_name,
                                                 initial_role__lt=2)
            if len(people) == 1:
                person = people[0]

        if person:

            g = Group.objects.get(name='NGT {}'.format(person.get_initial_role_display()))
            g.user_set.add(user)
            user.is_active = True

            # Assign the current user to the Person found
            person.user = user
            person.save()

        else:
            EmailMessage(
                subject=' {} requesting activation'.format(get_setting("EMAIL_SUBJECT_PREFIX"), user.get_full_name()),
                body="""Dear NGEE Tropics Admins,

User {} is requesting access to NGEE Tropics Archive service.

            """.format(user.get_full_name()),
                to=[get_setting("EMAIL_NGEET_TEAM")],
                reply_to=[get_setting("EMAIL_NGEET_TEAM")]).send()


# This signal is sent after users log in with default django authentication
user_logged_in.connect(notify_admin_to_activate_user)

# FROM https://pythonhosted.org/django-auth-ldap/reference.html#django_auth_ldap.backend.LDAPBackend.get_or_create_user
# This is a Django signal that is sent when clients should perform additional
# customization of a User object. It is sent after a user has been authenticated
# and the backend has finished populating it, and just before it is saved. The
# client may take this opportunity to populate additional model fields, perhaps
# based on ldap_user.attrs. This signal has two keyword arguments: user is the
# User object and ldap_user is the same as user.ldap_user. The sender is the LDAPBackend class.
django_auth_ldap.backend.populate_user.connect(notify_admin_to_activate_user)


def dataset_notify_status_change(sender, **kwargs):
    instance = kwargs['instance']
    original_status = kwargs['original_status']
    request = kwargs['request']
    root_url = "{}://{}".format(request.scheme, request.get_host())
    content = None

    if original_status != instance.status:
        if original_status is None and instance.status == permissions.DRAFT:
            dataset_name = instance.name
            if not dataset_name:
                dataset_name = "Unnamed"

            # this is a draft.
            content = """Dear {fullname},

The dataset {dataset_id}:{dataset_name} has been saved as a draft in the NGEE Tropics Archive. The dataset can be viewed at {root_url}.

Contact the  NGEE Tropics Archive Team (ngee-tropics-archive@googlegroups.com) for questions. Thanks for submitting your data to the NGEE Tropics Archive!

Sincerely
The NGEE Tropics Archive Team
""".format(**{"fullname": instance.created_by.get_full_name(), "dataset_id": instance.data_set_id(),
              "dataset_name": dataset_name, "root_url": root_url})
        elif original_status == permissions.DRAFT and instance.status == permissions.SUBMITTED:
            content = """"Dear {},

The dataset {}:{} created on {:%m/%d/%Y} was submitted to the NGEE Tropics Archive. The dataset can be viewed at {}.

You will be notified once the dataset has been approved or if we have questions regarding your submission.
Note that at this time we do not have the ability to edit the dataset once it has been approved.

Contact the  NGEE Tropics Archive Team (ngee-tropics-archive@googlegroups.com) for questions or if you want to make any changes to your dataset. Thanks for submitting your data to the NGEE Tropics Archive!

Sincerely
The NGEE Tropics Archive Team

"""

        elif original_status == permissions.SUBMITTED and instance.status == permissions.APPROVED:
            content = """Dear {},

The dataset {}:{}  created on {:%m/%d/%Y} has been approved for release. The dataset can be viewed at {}.

Contact the NGEE Tropics Archive Team (ngee-tropics-archive@googlegroups.com) for questions. Thanks for submitting your data to the NGEE Tropics Archive!

Sincerely
The NGEE Tropics Archive Team
"""
        else:
            pass  # do nothing for now

        if content:
            content = content.format(instance.created_by.get_full_name(), instance.data_set_id(), instance.name,
                                     instance.created_date, root_url)

    if content:
        EmailMessage(
            subject='{} Dataset {} ({})'.format(get_setting("EMAIL_SUBJECT_PREFIX"),
                                                archive_api.models.STATUS_CHOICES[int(instance.status)][1],
                                                           instance.data_set_id()),
            body=content,
            to=[instance.created_by.email],
            cc=[get_setting("EMAIL_NGEET_TEAM")],
            reply_to=[get_setting("EMAIL_NGEET_TEAM")]).send()


dataset_status_change.connect(dataset_notify_status_change)
