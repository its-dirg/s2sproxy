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


Configuration
=============

The configuration consists is managed two files, ``server_conf.py`` and
``proxy_conf.py``.

To setup the proxy server, copy ``server_conf.py.example`` to
``server_conf.py`` and ``proxy_conf.py.example`` to ``proxy_conf.py``.
See the comments in each file and modify the necessary parameters.

Running it
==========

The proxy only supports Python 3, and can be started with:
::

    python3 -m s2sproxy proxy_conf server_conf
