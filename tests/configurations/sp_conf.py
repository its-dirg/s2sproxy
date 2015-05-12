from saml2 import BINDING_HTTP_REDIRECT
from saml2 import BINDING_HTTP_POST


BASE = "http://example.com"

CONFIG = {
    "entityid": "{}/unittest_sp.xml".format(BASE),
    "service": {
        "sp": {
            "endpoints": {
                "assertion_consumer_service": [
                    ("%s/acs/redirect" % BASE, BINDING_HTTP_REDIRECT),
                    ("%s/acs/post" % BASE, BINDING_HTTP_POST)
                ],
            },
            "allow_unsolicited": "true",
        },
    },
    "cert_file": "pki/cert.pem",
    "key_file": "pki/key.pem",
    "metadata": {"local": ["configurations/proxy.xml"]},
}
