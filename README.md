# Auth0 Single Sign On Dashboard
A python flask implementation of an SSO dashboard.  OIDC for authentication and message bus for alert pipelines.

[![Build Status](https://travis-ci.org/mozilla-iam/sso-dashboard.svg?branch=master)](https://travis-ci.org/mozilla-iam/sso-dashboard)

!['dashboard.png'](docs/images/dashboard.png)
> Above is the dashboard prototype as it exists today. This screenshot will be updated as the dashboard UI evolves.

# Contributors

* Andrew Krug [:andrew] akrug@mozilla.com

# Projects this Project Uses

* Flask
* Redis
* Jinja
* Flask-SSE
* Gunicorn
* MUI-CSS Framework

# Features

* Server Side Events Security Alerts
* Control over what apps a user sees
* User profile editor
* Global Security Alerts
* IHaveBeenPwned Integration
* User alert acknowledgement/escalation

# Authentication Flow

All authentications are performed to auth0.  Due to the nature of the Application
this will be restricted to Mozilla LDAP login only until the "enriched profile"
is complete.

# Authorization Flow
This app does not technically provide authorization.  It does however check a
file using rule syntax to determine what applications should be in the users
dashboard.  The rule file exists in _dashboard/data/apps.yml_.

## Sample rule file syntax

```
---
apps:
  - application:
      name: "Demo App 1"
      op: okta
      url: "https://foo.bar.com"
      logo: "static/img/auth0.png"
      authorized_users: []
      authorized_groups: []
      display: false
```

> During authorization the app checks the users ldap group membership if a user
is member of the required ldap group and it exists in their profile the user is
shown the icon.

__Note: The display false attribute will cause the app not to be displayed at
all under any circumstance.  This exists largely to facilitate dev apps or
app staging and then taking apps live.__

# Adding apps to the Dashboard

In order to add applications to the dashboard there is an apps.yml file and
a logos directory that exists in the Mozilla-IAM github org.  

https://github.com/mozilla-iam/sso-dashboard-configuration

# Logos
These are the rules of the logos.  They have to conform to some standards due
to the fact they are in a responsive grid.

1. Logos should be uploaded to s3 bucket
2. Logos should 120px by 40px ( or same aspect )
3. Logos should be .png
