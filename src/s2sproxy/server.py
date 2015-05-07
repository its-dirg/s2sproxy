#!/usr/bin/env python
import argparse
import logging
import mimetypes
import os
import re
import sys
import traceback
import importlib

from saml2.config import config_factory
from saml2.httputil import Response, Unauthorized
from saml2.httputil import NotFound
from saml2.httputil import ServiceError
from s2sproxy.back import SamlSP
from s2sproxy.front import SamlIDP
from s2sproxy.util.config import get_configurations

LOGGER = logging.getLogger("")
LOGFILE_NAME = 's2s.log'
hdlr = logging.FileHandler(LOGFILE_NAME)
base_formatter = logging.Formatter(
    "%(asctime)s %(name)s:%(levelname)s %(message)s")

hdlr.setFormatter(base_formatter)
LOGGER.addHandler(hdlr)
LOGGER.setLevel(logging.DEBUG)

IDP = None
SP = None
Config = None

# ==============================================================================


class WsgiApplication(object, ):

    def __init__(self, args, static_dir):
        self.urls = []
        self.cache = {}
        self.static_dir = static_dir
        self.debug = args.debug

        # read the configuration file
        config = importlib.import_module(args.config)

        # deal with metadata only once
        _metadata_conf = config.CONFIG["metadata"]
        _spc = config_factory("sp", args.config)
        mds = _spc.load_metadata(_metadata_conf)
        _spc.metadata = mds
        idp_conf, sp_conf = get_configurations(args.config, metadata_construction=False, metadata=mds, cache=self.cache)

        self.config = {
            "SP": _spc,
            "IDP": idp_conf
        }

        sp = SamlSP(None, None, self.config["SP"], self.cache)
        self.urls.extend(sp.register_endpoints())

        idp = SamlIDP(None, None, self.config["IDP"], self.cache, None)
        self.urls.extend(idp.register_endpoints())

        # If entityID is set it means this is a proxy in front of one IdP
        if args.entityid:
            self.entity_id = args.entityid
            self.sp_args = {}
        else:
            self.entity_id = None
            self.sp_args = {"discosrv": config.DISCO_SRV}

    def incomming(self, info, instance, environ, start_response, relay_state):
        """
        An Authentication request has been requested, this is the second step
        in the sequence

        :param info: Information about the authentication request
        :param instance: IDP instance that received the Authentication request
        :param environ: WSGI environment
        :param start_response: WSGI start_response
        :param relay_state:

        :return: response
        """

        # If I know which IdP to authenticate at return a redirect to it
        if self.entity_id:
            inst = SamlSP(environ, start_response, self.config["SP"], self.cache, self.outgoing)
            state_key = inst.store_state(info["authn_req"], relay_state,
                                         info["req_args"])
            return inst.authn_request(self.entity_id, state_key)
        else:
            # start the process by finding out which IdP to authenticate at
            return instance.disco_query(info["authn_request"], relay_state,
                                        info["req_args"])


    def outgoing(self, response, instance):
        """
        An authentication response has been received and now an authentication
        response from this server should be constructed.

        :param response: The Authentication response
        :param instance: SP instance that received the authentication response
        :return: response
        """

        _idp = SamlIDP(instance.environ, instance.start_response,
                       self.config["SP"], self.cache, self.outgoing)

        _state = instance.sp.state[response.in_response_to]
        orig_authn_req, relay_state, req_args = instance.sp.state[_state]

        # The Subject NameID
        subject = response.get_subject()
        # Diverse arguments needed to construct the response
        resp_args = _idp.idp.response_args(orig_authn_req)

        # Slightly awkward, should be done better
        _authn_info = response.authn_info()[0]
        _authn = {"class_ref": _authn_info[0], "authn_auth": _authn_info[1][0]}

        # This is where any possible modification of the assertion is made

        # Will signed the response by default
        resp = _idp.construct_authn_response(
            response.ava, name_id=subject, authn=_authn,
            resp_args=resp_args, relay_state=relay_state, sign_response=True)

        return resp

    # ==============================================================================


    def static(self, environ, start_response, path):
        full_path = os.path.join(self.static_dir, os.path.normpath(path))

        if os.path.exists(full_path):
            with open(full_path, 'rb') as f:
                content = f.read()

            content_type, encoding = mimetypes.guess_type(full_path)
            headers = [('Content-Type', content_type)]
            start_response("200 OK", headers)
            return [content]
        else:
            response = NotFound(
                "File '{}' not found.".format(environ['PATH_INFO']))
            return response(environ, start_response)

    def run_entity(self, spec, environ, start_response):
        """
        Picks entity and method to run by that entity.

        :param spec: a tuple (entity_type, response_type, binding)
        :param environ: WSGI environ
        :param start_response: WSGI start_response
        :return:
        """

        if isinstance(spec, tuple):
            if spec[0] == "SP":
                inst = SamlSP(environ, start_response, self.config["SP"], self.cache,
                              self.outgoing, **self.sp_args)
            else:
                inst = SamlIDP(environ, start_response, self.config["IDP"], self.cache,
                               self.incomming)

            func = getattr(inst, spec[1])
            return func(*spec[2:])
        else:
            return spec()


    def run_server(self, environ, start_response):
        """
        The main WSGI application.

        If nothing matches return NotFound.

        :param environ: The HTTP application environment
        :param start_response: The application to run when the handling of the
            request is done
        :return: The response as a list of lines
        """

        path = environ.get('PATH_INFO', '').lstrip('/')
        if ".." in path:
            resp = Unauthorized()
            return resp(environ, start_response)

        if path.startswith("robots.txt"):
            return self.static(environ, start_response, "robots.txt")
        if path.startswith("static/"):
            path = path.lstrip("static/")
            return self.static(environ, start_response, path)

        for regex, spec in self.urls:
            match = re.search(regex, path)
            if match is not None:
                try:
                    environ['oic.url_args'] = match.groups()[0]
                except IndexError:
                    environ['oic.url_args'] = path

                try:
                    return self.run_entity(spec, environ, start_response)
                except Exception as err:
                    if not self.debug:
                        print >> sys.stderr, "%s" % err
                        traceback.print_exc()
                        LOGGER.exception("%s" % err)
                        resp = ServiceError("%s" % err)
                        return resp(environ, start_response)
                    else:
                        raise

        LOGGER.debug("unknown side: %s" % path)
        resp = NotFound("Couldn't find the side you asked for!")
        return resp(environ, start_response)
