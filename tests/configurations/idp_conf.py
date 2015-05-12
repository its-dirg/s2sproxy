#!/usr/bin/env python
# -*- coding: utf-8 -*-

from saml2 import BINDING_HTTP_REDIRECT
from saml2 import BINDING_HTTP_POST


BASE = "http://example.com"

CONFIG = {
    "entityid": "{}/unittest_idp.xml".format(BASE),
    "service": {
        "idp": {
            "endpoints": {
                "single_sign_on_service": [
                    ("%s/sso/post" % BASE, BINDING_HTTP_POST),
                    ("%s/sso/redirect" % BASE, BINDING_HTTP_REDIRECT),
                ],
            },
        },
    },
    "key_file": "pki/key.pem",
    "cert_file": "pki/cert.pem",
    "metadata": {
        "local": ["configurations/proxy.xml"]
    },
}