from os import path

__author__ = 'haho0032'

import cherrypy
from cherrypy.test import helper
import tests.configurations.proxy_server_conf_local as proxy_server_conf_local
from beaker.middleware import SessionMiddleware
from s2sproxy.server import WsgiApplication
from argparse import Namespace


class AliveTestCase(helper.CPWebCase):

    ARGS = Namespace(debug=False,
                     entityid=None,
                     config="pefim_proxy_conf_local",
                     server_config="pefim_server_conf_local")

    WSGI_APP = WsgiApplication(ARGS, base_dir=path.dirname(path.realpath(__file__)) + "/../")

    @staticmethod
    def application(environ, start_response):
        return AliveTestCase.WSGI_APP.run_server(environ, start_response)

    def setup_server():
        cherrypy.tree.graft(SessionMiddleware(AliveTestCase.application, proxy_server_conf_local.SESSION_OPTS), '/')

    setup_server = staticmethod(setup_server)

    def test_server_is_alive(self):
        self.getPage("/static/alive.txt")
        self.assertStatus('200 OK')
        self.assertHeader('Content-Type', 'text/plain')
        self.assertBody('ALIVE')

    def test_server_robots(self):
        self.getPage("/robots.txt")
        self.assertStatus('200 OK')
        self.assertHeader('Content-Type', 'text/plain')
        self.assertBody('User-agent: *\nDisallow: /\n')
        self.getPage("/whatever/all/pages/robots.txt")
        self.assertStatus('200 OK')
        self.assertHeader('Content-Type', 'text/plain')
        self.assertBody('User-agent: *\nDisallow: /\n')

    def test_server_404(self):
        self.getPage("/whater/page/do/not/exist")
        self.assertStatus('404 NOT FOUND')
        self.assertHeader('Content-Type', 'text/html')