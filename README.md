# s2sproxy
SAML2 to SAML2 proxy

[![Build Status](https://travis-ci.org/its-dirg/s2sproxy.svg?branch=master)](https://travis-ci.org/its-dirg/s2sproxy)

A Simple proxy from SAML2 to SAML2.
Ultimately this proxy will be able to achieve the following things:

* Hiding bad SP or IdP behavior.
* Adding information to or filtering assertions.
* Adding an extra authentication factor.

## Installation

    git clone https://github.com/its-dirg/s2sproxy
    cd s2sproxy
    pip install .
    pip install -r requirements.txt # additional dependencies to run the server
    
``pysaml2`` (which is a dependency of this proxy) also requires ``xmlsec1``, which can be installed on
Ubuntu with:

    apt-get install xmlsec1


## Configuration

The configuration of the proxy is managed in ``proxy_conf.py``, while the webserver
running the proxy application is managed in ``server_conf.py``. See below for configuration
details for ``mod_wsgi`` for Apache HTTP Server (Apache).

To setup the proxy server, copy ``example/server_conf.py.example`` to
``server_conf.py`` and ``example/proxy_conf.py.example`` to ``proxy_conf.py``.
See the comments in each file and modify the parameters as necessary.

Important parameters:

* Server info: ``HOST`` and ``PORT`` in both ``proxy_conf.py`` and ``server_conf.py`
* xmlsec binary: ``xmlsec_path`` in ``proxy_conf.py``
* Url for discovery server: ``DISCO_SRV`` in ``proxy_conf.py`` (or ``-e`` command line parameter for proxy in front of a single IdP)
* Attribute transformation module: ``ATTRIBUTE_MODULE`` in ``proxy_conf.py``
* Private key and certificate for SAML: ``CONFIG["key_file"]`` and ``CONFIG["key_file"]`` in ``proxy_conf.py``
* Metadata for SP's and IdP's communicating with the proxy: ``CONFIG["metadata"]`` in ``proxy_conf.py``
* SSL/TLS certificates (for https): ``SERVER_KEY``, ``SERVER_CERT``, ``CERT_CHAIN``

### Generate metadata

SAML metadata for the frontend SP and backend IdP of the proxy can be generated with the
``make_metadata.py`` script bundled with pysaml2:

    [<optional virtualenv path>/]make_metadata.py proxy_conf > proxy.xml

## Running it

The proxy only supports Python 3, and can be started with:

    python3 -m s2sproxy proxy_conf server_conf

If you want to use the example certs/keys provided, make sure the current working directory is 
``example/`` and that it contains your modified configuration files before running the above command. 

## Integration with mod_wsgi

A version of mod_wsgi that supports Python 3 is required.

Copy ``example/proxy_mod_wsgi.wsgi`` to ``/usr/local/www/wsgi/proxy.wsgi`` or your preferred
location for mod_wsgi scripts. Create the directories ``/var/log/s2sproxy`` and ``/var/cache/s2sproxy``
with sufficient permissions so that the Apache process can write
to them. Copy ``example/proxy_mod_wsgi_config.py.example`` to ``/etc/s2sproxy/config.py``
and edit as appropriate for your deployment.

Edit your Apache configuration to mount the WSGI script, for example:

    # Allow access to the WSGI application.
    <Directory /usr/local/www/wsgi>
        AllowOverride None
        Require all granted
    </Directory>

    # Mount the proxy WSGI application at root of virtual host.
    WSGIScriptAlias / /usr/local/www/wsgi/proxy.wsgi
