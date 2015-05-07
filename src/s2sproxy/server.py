#!/usr/bin/env python
import argparse
import logging
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

    def __init__(self, args, base_dir):
        self.urls = [(r'.+\.css$', WsgiApplication.css), ]
        self.cache = {}

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
        LOGGER.info("[static]sending: %s" % (path,))

        try:
            text = open(path).read()
            if path.endswith(".ico"):
                start_response('200 OK', [('Content-Type', "image/x-icon")])
            elif path.endswith(".html"):
                start_response('200 OK', [('Content-Type', 'text/html')])
            elif path.endswith(".json"):
                start_response('200 OK', [('Content-Type', 'application/json')])
            elif path.endswith(".txt"):
                start_response('200 OK', [('Content-Type', 'text/plain')])
            elif path.endswith(".css"):
                start_response('200 OK', [('Content-Type', 'text/css')])
            else:
                start_response('200 OK', [('Content-Type', "text/xml")])
            return [text]
        except IOError:
            resp = NotFound()
            return resp(environ, start_response)

    @staticmethod
    def css(environ, start_response):
        try:
            info = open(environ["PATH_INFO"]).read()
            resp = Response(info)
        except (OSError, IOError):
            resp = NotFound(environ["PATH_INFO"])

        return resp(environ, start_response)

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

        # if path == "robots.txt":
        #     return static(environ, start_response, "static/robots.txt")
        # elif path.startswith("static/"):
        #     return static(environ, start_response, path)

        for regex, spec in self.urls:
            match = re.search(regex, path)
            if match is not None:
                try:
                    environ['oic.url_args'] = match.groups()[0]
                except IndexError:
                    environ['oic.url_args'] = path

                try:
                    return self.run_entity(spec, environ, start_response)
                except Exception, err:
                    print >> sys.stderr, "%s" % err
                    message = traceback.format_exception(*sys.exc_info())
                    print >> sys.stderr, message
                    LOGGER.exception("%s" % err)
                    resp = ServiceError("%s" % err)
                    return resp(environ, start_response)

        LOGGER.debug("unknown side: %s" % path)
        resp = NotFound("Couldn't find the side you asked for!")
        return resp(environ, start_response)

    @staticmethod
    def arg_parser(args=None, error=None, exception=None):
        #Read arguments.
        parser = argparse.ArgumentParser()
        #True if the server should save debug logs.
        parser.add_argument('-d', dest='debug', action='store_true', help="Not implemented yet.")
        parser.add_argument('-pe', dest='pe', action='store_true', help="Add this flag to print the exception that "
                                                                        "that is the reason for an invalid "
                                                                        "configuration error.")
        parser.add_argument('-e', dest="entityid", help="Entity id for the underlying IdP if only one IdP should be"
                                                        " used. Otherwise will a discovery server be used.")
        # parser.add_argument('-e_alg', dest="e_alg", help="Encryption algorithm to be used for target id 2. "
        #                                                  "Approved values: aes_128_cbc, aes_128_cfb, aes_128_ecb, "
        #                                                  "aes_192_cbc, aes_192_cfb, aes_192_ecb, aes_256_cbc, "
        #                                                  "aes_256_cfb and aes_256_ecb"
        #                                                  "Default is aes_128_cbc if flag is left out.")
        # parser.add_argument('-key', dest="key", help="Encryption key to be used for target id2."
        #                                              "Approved values is a valid key for the chosen encryption "
        #                                              "algorithm in e_alg.")
        # parser.add_argument('-h_alg', dest="h_alg", help="Hash algorithm to be used for target id 2 and the proxy "
        #                                                  "userid. Approved values: md5, sha1, sha224, sha256, sha384, "
        #                                                  "sha512 Default is sha256 if flag is left out.")
        # parser.add_argument('-iv', dest="iv", help="Initialization vector to be used for the encryption. "
        #                                            "Default is to create a random value for each call if the "
        #                                            "encrypted messages can be saved, otherwise will the same "
        #                                            "random value be used for each call. If the same iv is to be"
        #                                            " used each call its recommended to assign a value to make "
        #                                            "sure the same iv is used if the server restart.")
        parser.add_argument(dest="config", help="Configuration file for the pysaml sp and idp.")
        parser.add_argument(dest="server_config", help="Configuration file with server settings.")
        if args is not None:
            args = parser.parse_args(args)
        else:
            args = parser.parse_args()
        if error:
            if args.pe:
                error += "\n%s" % exception
            parser.error(error)

        # valid, message = WsgiApplication.validate_server_config(args)
        # if not valid:
        #     parser.error(message)
        # valid, message = WsgiApplication.validate_config(args)
        # if not valid:
        #     parser.error(message)
        return args

    # ----------------------------------------------------------------------


# if __name__ == '__main__':
#     import argparse
#     import importlib
#
#     from cherrypy import wsgiserver
#     from cherrypy.wsgiserver import ssl_pyopenssl
#
#     parser = argparse.ArgumentParser()
#     parser.add_argument('-d', dest='debug', action='store_true')
#     parser.add_argument('-e', dest="entityid")
#     parser.add_argument(dest="config")
#     args = parser.parse_args()
#
#     # read the configuration file
#     sys.path.insert(0, ".")
#     Config = importlib.import_module(args.config)
#
#
#     # ============== Web server ===============
#
#     SRV = wsgiserver.CherryPyWSGIServer((Config.HOST, Config.PORT), application)
#
#     if Config.HTTPS:
#         SRV.ssl_adapter = ssl_pyopenssl.pyOpenSSLAdapter(
#             Config.SERVER_CERT, Config.SERVER_KEY, Config.CERT_CHAIN)
#
#     LOGGER.info("Server starting")
#     if Config.HTTPS:
#         print "S2S listening on %s:%s using HTTPS" % (Config.HOST, Config.PORT)
#     else:
#         print "S2S listening on %s:%s" % (Config.HOST, Config.PORT)
#
#     try:
#         SRV.start()
#     except KeyboardInterrupt:
#         SRV.stop()








# if __name__ == '__main__':
#     import argparse
#     import importlib
#
#     from cherrypy import wsgiserver
#     from cherrypy.wsgiserver import ssl_pyopenssl
#
#     parser = argparse.ArgumentParser()
#     parser.add_argument('-d', dest='debug', action='store_true')
#     parser.add_argument('-e', dest="entityid")
#     parser.add_argument(dest="config")
#     args = parser.parse_args()
#
#     # read the configuration file
#     sys.path.insert(0, ".")
#     Config = importlib.import_module(args.config)
#
#     # deal with metadata only once
#     _metadata_conf = Config.CONFIG["metadata"]
#     Config.CONFIG["metadata"] = {}
#
#     CONFIG = {
#         "SP": config_factory("sp", args.config),
#         "IDP": config_factory("idp", args.config)}
#
#     _spc = CONFIG["SP"]
#     mds = _spc.load_metadata(_metadata_conf)
#
#     CONFIG["SP"].metadata = mds
#     CONFIG["IDP"].metadata = mds
#
#     # If entityID is set it means this is a proxy in front of one IdP
#     if args.entityid:
#         EntityID = args.entityid
#         SP_ARGS = {}
#     else:
#         EntityID = None
#         SP_ARGS = {"discosrv": Config.DISCO_SRV}
#
#     CACHE = {}
#     sp = SamlSP(None, None, CONFIG["SP"], CACHE)
#     URLS.extend(sp.register_endpoints())
#
#     idp = SamlIDP(None, None, CONFIG["IDP"], CACHE, None)
#     URLS.extend(idp.register_endpoints())
#
#     # ============== Web server ===============
#
#     SRV = wsgiserver.CherryPyWSGIServer((Config.HOST, Config.PORT), application)
#
#     if Config.HTTPS:
#         SRV.ssl_adapter = ssl_pyopenssl.pyOpenSSLAdapter(
#             Config.SERVER_CERT, Config.SERVER_KEY, Config.CERT_CHAIN)
#
#     LOGGER.info("Server starting")
#     if Config.HTTPS:
#         print "S2S listening on %s:%s using HTTPS" % (Config.HOST, Config.PORT)
#     else:
#         print "S2S listening on %s:%s" % (Config.HOST, Config.PORT)
#
#     try:
#         SRV.start()
#     except KeyboardInterrupt:
#         SRV.stop()
