# s2sproxy
SAML2 to SAML2 proxy

[![Build Status](https://travis-ci.org/its-dirg/s2sproxy.svg?branch=master)](https://travis-ci.org/its-dirg/s2sproxy)

A Simple proxy from SAML2 to SAML2.
Ultimately this proxy will be possible to use to accomplish these things:

* Hiding bad SP or IdP behavior.
* Adding information to or filtering assertions.
* Adding an extra authentication factor.

Installation
============

::

    git clone https://github.com/its-dirg/s2sproxy
    cd s2sproxy
    pip install .
    pip install -r requirements.txt # additional dependencies to run the server
    
pysaml2 also requires ``xmlsec1``, which can be installed on Ubuntu with::

    apt-get install xmlsec1


Configuration
=============

The configuration consists is managed two files, ``server_conf.py`` and
``proxy_conf.py``.

To setup the proxy server, copy ``example/server_conf.py.example`` to
``server_conf.py`` and ``example/proxy_conf.py.example`` to ``proxy_conf.py``.
See the comments in each file and modify the parameters as necessary.

Important parameters:

* Server info: ``HOST`` and ``PORT`` in both ``proxy_conf.py`` and ``server_conf.py`
* xmlsec binary: ``xmlsec_path`` in ``proxy_conf.py``
* Url for discovery server: ``DISCO_SRV`` in ``proxy_conf.py`` or ``-e`` command line parameter
* Attribute transformation module: ``ATTRIBUTE_MODULE`` in ``proxy_conf.py``
* Private key and certificate for SAML: ``CONFIG["key_file"]`` and ``CONFIG["key_file"]`` in ``proxy_conf.py``
* Metadata for SP's and IdP's: ``CONFIG["metadata"]`` in ``proxy_conf.py``
* SSL/TLS certificates (for https): ``SERVER_KEY``, ``SERVER_CERT``, ``CERT_CHAIN``

Running it
==========

The proxy only supports Python 3, and can be started with:
::

    python3 -m s2sproxy proxy_conf server_conf
