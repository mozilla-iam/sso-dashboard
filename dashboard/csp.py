import json


DASHBOARD_CSP = {
    'default-src': [
        '\'self\'',
    ],
    'script-src': [
        '\'self\'',
        'ajax.googleapis.com',
        'fonts.googleapis.com',
        'https://*.googletagmanager.com',
        'https://tagmanager.google.com',
        'https://*.google-analytics.com',
        'https://cdn.sso.mozilla.com',
        'https://cdn.sso.allizom.org'
    ],
    'style-src': [
        '\'self\'',
        'ajax.googleapis.com',
        'fonts.googleapis.com',
        'https://cdn.sso.mozilla.com',
        'https://cdn.sso.allizom.org'
    ],
    'img-src': [
        '\'self\'',
        'https://mozillians.org',
        'https://media.mozillians.org',
        'https://cdn.mozillians.org',
        'https://cdn.sso.mozilla.com',
        'https://cdn.sso.allizom.org',
        'https://*.google-analytics.com',
        'https://*.gravatar.com',
        'https://i0.wp.com/'
    ],
    'font-src': [
        '\'self\'',
        'fonts.googleapis.com',
        'fonts.gstatic.com',
        'https://cdn.sso.mozilla.com',
        'https://cdn.sso.allizom.org'
    ]
}
