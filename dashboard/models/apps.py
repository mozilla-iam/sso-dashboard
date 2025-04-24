"""
These specs are copied to sso-dashboard-configuration/tests/test_yaml.py.

If you change these definitions, copy them over there as well.
"""

from typing import Literal, NotRequired, TypedDict


class Application(TypedDict):
    """
    A schema(ish) definition for what we expect typical applications to
    look like.
    """

    # RP's name, easier for humans when reading this file.
    name: str

    # The access provider name (OP: Open Id Connect Provider). They are all
    # "auth0" currently but that might change someday.
    op: Literal["auth0"]

    # This is the URL that a user must visit to be logged into the RP. This
    # URL would either be the URL of the login button on the site (if it has
    # one), or the URL that a user gets redirected to when they visit a
    # protected page while unauthenticated.
    url: str

    # A custom logo to be displayed for this RP on the SSO Dashboard.
    # Loaded from the same CDN as `apps.yml`, under the `images/` directory.
    logo: str

    # If true, will be displayed on the SSO Dashboard
    display: bool

    # The access provider's `client_id` for this RP.
    client_id: NotRequired[str]

    # An URL that people can bookmark on the SSO Dashboard to login directly to
    # that RP (i.e. not the RP frontpage).
    # e.g. /box -> redirect to Box's authentication page.
    vanity_url: NotRequired[list[str]]

    # The list of users and groups allowed to access this RP.
    # If both authorize_users and authorized_groups are empty, everyone is
    # allowed.
    # If one is empty and the other has content, only the members of the non
    # empty one are allowed.
    # If both have content, the union of everyone in both are allowed.
    #
    # The dashboard uses this to decide if we should show the tile to the user.
    # Our IdP uses this to decide if a user is authorized to access this
    # application.
    authorized_users: list[str]
    authorized_groups: list[str]

    # See: https://infosec.mozilla.org/guidelines/risk/standard_levels
    #
    # AAL values below are available at the IAM well-known endpoint
    # See: (https://auth.mozilla.org/.well-known/mozilla-iam)
    #
    # AAI is Authenticator Assurance Indicator: A Standard level which
    # indicates the amount confidence in the authentication mechanism used is
    # required to access this RP. It is enforced by the Access Provider.
    # E.g. MEDIUM may mean 2FA required
    AAL: NotRequired[Literal["LOW", "MEDIUM", "MAXIMUM"]]


class AppEntry(TypedDict):
    """An item in the `apps` list."""

    application: Application


class Apps(TypedDict):
    """The top-level definition of the apps.yml"""

    apps: list[AppEntry]
