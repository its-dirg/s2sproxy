#!/usr/bin/env python
# -*- coding: utf-8 -*-

from saml2 import BINDING_HTTP_REDIRECT
from saml2 import BINDING_HTTP_POST
from example.test_module import TestModule
from s2sproxy.util.attribute_module_base import SingleAttributeMatcher


BASE = 'https://example.com'

CONFIG = {
    "entityid": "{}/proxy.xml".format(BASE),
    "service": {
        "idp": {
            "endpoints": {
                "single_sign_on_service": [
                    ("%s/sso/redirect" % BASE, BINDING_HTTP_REDIRECT),
                    ("%s/sso/post" % BASE, BINDING_HTTP_POST),
                ],
            },
        },
        "sp": {
            "endpoints": {
                "assertion_consumer_service": [
                    ("%s/acs/post" % BASE, BINDING_HTTP_POST),
                    ("%s/acs/redirect" % BASE, BINDING_HTTP_REDIRECT)
                ],
            }
        },
    },
    "key_file": "pki/key.pem",
    "cert_file": "pki/cert.pem",
    "metadata": {
        "local": ["configurations/unittest_idp.xml",
                  "configurations/unittest_sp.xml"],
    },
    "attribute_module": TestModule("users.json", {"email": "mail",
                                                  "testA": "sn",
                                                  "university": "o"},
                                   SingleAttributeMatcher("mail", "email")),
}
