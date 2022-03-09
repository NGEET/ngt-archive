import django_auth_ldap.backend
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.signals import user_logged_in
from django.core.mail import EmailMessage
from django.db import transaction
from django.dispatch import Signal
from django.utils import timezone

import archive_api
from archive_api import permissions
from archive_api.models import DataSet, Person
from django.contrib.auth.models import update_last_login


EMAIL_FOOTER_FORMAT= """-----------------
More information.

- You can find more information about the NGEE-Tropics Data in this link:
https://ngee-tropics.lbl.gov/research/data/

- If you need other help with your account or access to the NGEE-Tropics Archive, please send a message detailing the issue to:
{ngeet_team}

- If you would like to change your password, please access:
https://ameriflux-data.lbl.gov/Pages/ResetFluxPassword.aspx

- If you have forgotten your login, please access:
https://ameriflux-data.lbl.gov/Pages/ForgotFluxUsername.aspx"""


# Signal for Dataset Status changes
dataset_status_change = Signal(providing_args=['request', 'user', 'instance', 'original_status'])


def get_setting(setting_name):
    """
    Get the settings value if it exists
    :param setting_name:
    :return:
    """
    return settings.ARCHIVE_API[setting_name]


def notify_new_account(sender, user, **kwargs):
    """
    After the user is authenticated check to see if they have any groups. If they do
    not, look them up in the Person table.  If they exist, add them to the 'NGT Team' or 'NGT Collaborator' group.

    The Person must have a role of Collaborator or Team

    :param sender:
    :param user:
    :param kwargs:
    :return:
    """
    from archive_api.models import NGTUser
    if not user.id:
        user.save()

    ngt_user = NGTUser.objects.get(id = user.id)
    email_footer = EMAIL_FOOTER_FORMAT.format(**{"ngeet_team":get_setting("EMAIL_NGEET_TEAM")})

    # Has the user been activated to access the NGEE Tropics
    # Data Collection?
    if not ngt_user.is_activated and not user.is_superuser:
        # check existing list
        # if not in any of these groups send email to admins

        person = None
        try:
            try:
                person = Person.objects.get(user = user)
            except Person.DoesNotExist:
                if user.email:
                    person = Person.objects.get(email=user.email, user_role__lt=2)  # Person is a collaborator or team
        except Person.DoesNotExist:
            pass # Do nothing

        # They can only be activated if they have been assigned a user role and there is
        # no user assined
        if person and person.user_role is not None and person.user is None:

            with transaction.atomic():
                # only add a them to a group if they don't have one
                if len(user.groups.all()) == 0:
                    g = Group.objects.get(name='NGT {}'.format(person.get_user_role_display()))
                    g.user_set.add(user)

                # Assign the current user to the Person found
                person.user = user
                person.save()

        elif not user.last_login:
            # Make sure the activation request is only sent once
            EmailMessage(
                subject=f"{get_setting('EMAIL_SUBJECT_PREFIX')} NGEE-Tropics Account Created for '{user.username}'",
                to=[user.email],
                cc=get_setting("EMAIL_NGEET_TEAM"),
                reply_to=get_setting("EMAIL_NGEET_TEAM"),
                body=f"""Greetings {user.username},

Your access to the NGEE-Tropics Archive has been configured and you can now download data from the portal. Thank you for your participation in this project.

You can access the portal datasets using this link:
https://ngt-data.lbl.gov/dois


------------------
Contributing data.

If you also want the ability to contribute/upload data packages to the NGEE-Tropics Archive or access other team resources, please send the information below to ngee-tropics-archive@lbl.gov
- First/Last name
- Email address
- Your ORCID (to create one, access: https://orcid.org/)
- Your Affiliation/Institution
- Indicated if you are funded by NGEE-Tropics: Yes/No (note that NGEE-Tropics collaborators, even if not funded by the project, are welcome to deposit their data with the archive)


{email_footer}
            """).send()

        # Any authenticated use should be set as active
        # This will allow access to download public datasets
        # Only set this the first time users login. This will
        # allow problem users to be banned, if needed.
        if not user.is_active and not user.last_login:
            user.is_active = True
            user.save()

        # Now set the last_login time
        update_last_login(sender, user, **kwargs)


# This signal is sent after users log in with default django authentication
#     Disconnect the signal that updates last_login
user_logged_in.disconnect(update_last_login, dispatch_uid='update_last_login')
user_logged_in.connect(notify_new_account)

# FROM https://pythonhosted.org/django-auth-ldap/reference.html#django_auth_ldap.backend.LDAPBackend.get_or_create_user
# This is a Django signal that is sent to the user to confirm that a new
# account was created. It is sent after a user has been authenticated
# and the backend has finished populating it, and just before it is saved.
# This signal has two keyword arguments: user is the
# User object and ldap_user is the same as user.ldap_user. The sender is the LDAPBackend class.
django_auth_ldap.backend.populate_user.connect(notify_new_account)


def dataset_notify_status_change(sender, **kwargs):
    """
    New Steps and Emails
    The following workflow steps will be impelments

    1. NEW DATASET
    2. SAVE DRAFT - 1st save email
    3. SUBMIT - Submit email
    4. APPROVE - Approve email
    5. LIVE DATASET
    6. SAVE - Changes 1st change email
    7. REQUEST REVIEW - Submit email
    8. APPROVE - Approve email
    9. LIVE DATASET (updated)

    :param sender:
    :param kwargs:
    :return:
    """
    instance = kwargs['instance']
    original_status = kwargs['original_status']
    request = kwargs['request']
    root_url = "{}://{}".format(request.scheme, request.get_host())
    content = None
    ngeet_team = ",".join(get_setting("EMAIL_NGEET_TEAM"))
    fullname = instance.managed_by.get_full_name()
    dataset_id = instance.data_set_id()
    root_url = root_url
    created_date = instance.created_date
    dataset_name = instance.name
    email_footer = EMAIL_FOOTER_FORMAT.format(**{"ngeet_team": ngeet_team})
    if not dataset_name:
        dataset_name = "Unnamed"

    dataset_name = dataset_name.strip()

    DOI_CITATION = ""
    if instance.doi and not instance.publication_date:
        DOI_CITATION = f"""
The DOI ({instance.doi}) was issued for your dataset, but it is NOT ACTIVE at this 
time and cannot be accessed. The DOI will be activated when the dataset is approved, 
keeping the same DOI identifier/number. You can use this DOI to cite your dataset, 
this is an example citation for the dataset:

{instance.citation}
"""
    elif instance.doi:
        DOI_CITATION = f"""
The DOI ({instance.doi}) issued for the dataset at the submission step will be active 
and can be accessed within 24h. You can use this DOI to cite your dataset, 
this is an example citation for the dataset:

{instance.citation}
"""

    if original_status != instance.status:
        if instance.status == permissions.DRAFT and original_status is None:

            # Users FIRST SAVE (Step 2)
            content = f"""Greetings {fullname},

The dataset {dataset_id}:{dataset_name} has been saved as a draft in the NGEE-Tropics Archive, and can be viewed at {root_url}.

You can also login with your account credentials, select "Edit Drafts" and then click the "Edit" button for {dataset_id}:{dataset_name}.

If you have any questions, please contact us at:
{ngeet_team}

Thank you for contributing your data to the NGEE-Tropics Archive!

Sincerely,
The NGEE-Tropics Archive Team

{EMAIL_FOOTER_FORMAT}
"""
        elif instance.status == permissions.DRAFT:
            # USER FIRST CHANGES EMAIL template (Step 6)
            content = f"""Greetings {fullname},

The changes to the dataset {dataset_id}:{dataset_name} have been saved as a draft in 
the NGEE-Tropics Archive, and can be viewed at {root_url}.

You can also login with your account credentials, select "Edit Drafts" and then click 
the "Edit" button for {dataset_id}:{dataset_name}.

Note that these changes WILL ONLY BE PUBLISHED after a review process is requested. You 
can start the review process by clicking the “Request Review” button in the dataset page 
described above.

If you have any questions, please contact us at:
{ngeet_team}

Thank you for contributing your data to the NGEE-Tropics Archive!

Sincerely,
The NGEE-Tropics Archive Team


{email_footer}
"""
        elif instance.status == permissions.SUBMITTED:
            # USER SUBMIT EMAIL template (Step 3,7)
            content = f"""Greetings {fullname},

The dataset {dataset_id}:{dataset_name} created on {created_date:%m/%d/%Y} has been 
submitted to the NGEE-Tropics Archive.

We will start the review and publication processes for the dataset. As soon as the dataset has been approved, 
or in case we have any clarifying questions, you will be notified by email.

Note that the publication status will not prevent you from editing your data package. 
If you did not want to request that your data be published, please reply to this 
e-mail and we will stop the publication process.
{DOI_CITATION}
If you have any questions, please contact us at:
{ngeet_team}

Thank you for contributing your data to the NGEE-Tropics Archive!

Sincerely,
The NGEE-Tropics Archive Team

{email_footer}
"""

        elif instance.status == permissions.APPROVED:
            # NGEE-TROPICS APPROVE EMAIL template (Step 4)
            content = f"""Greetings {fullname},

The dataset {dataset_id}:{dataset_name} created on {created_date:%m/%d/%Y} has been approved 
for release and is now published.
{DOI_CITATION}
If you have any questions, please contact us at:
{ngeet_team}

Thank you for contributing your data to the NGEE-Tropics Archive!

Sincerely,
The NGEE-Tropics Archive Team

{email_footer}
"""
        else:
            pass  # do nothing for now

    if content:
        EmailMessage(
            subject='{} Dataset {} ({}) on {}'.format(get_setting("EMAIL_SUBJECT_PREFIX"),
                                                archive_api.models.STATUS_CHOICES[int(instance.status)][1],
                                                instance.data_set_id(),
                                                timezone.now().strftime("%Y-%m-%d %H:%M %Z")),
            body=content,
            to=[instance.managed_by.email],
            cc=get_setting("EMAIL_NGEET_TEAM"),
            reply_to=get_setting("EMAIL_NGEET_TEAM")).send()


dataset_status_change.connect(dataset_notify_status_change)
