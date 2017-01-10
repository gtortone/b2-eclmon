#!/usr/bin/env python
# to generate a SSL certificate:
# openssl req -x509 -newkey rsa:4096 -sha256 -nodes -keyout b2ecl-na.key -out b2ecl-na.crt  -days 3650
#
# to get base64 encoding of username:password to use in collectd.conf
# echo "admin:4dm1n" | base64

import os, sys
import tornado.httpserver
import ssl
import base64
import tornado.ioloop
import tornado.options
import tornado.web
import json, socket

from tornado.options import define, options
define("port", default=8000, help="run on the given port", type=int)
define("https", default="yes", help="enable http with SSL")
define("auth_user", default="admin", help="authentication username")
define("auth_pass", default="4dm1n", help="authentication password")
define("ssl_cert", default="ssl-cert.crt", help="SSL certificate file")
define("ssl_key", default="ssl-key.key", help="SSL key file")

debug = False
ghost = "localhost"	# modify here
gport = 2003

# base collectd metric format
# host "." plugin ["-" plugin instance] "/" type ["-" type instance]

class PutHandler(tornado.web.RequestHandler):
    def post(self):
        if debug: print(self.request.headers)

        auth_header = self.request.headers.get('Authorization')
	if auth_header is None: 
           if debug: print("no auth header")
	   return
        if not auth_header.startswith('Basic '): 
           if debug: print("no basic auth method")
	   return 

        auth_decoded = base64.decodestring(auth_header[6:])
        username, password = auth_decoded.split(':', 2)

        if username != options.auth_user or password != options.auth_pass:
           print("auth fail")
           return

        print("auth ok")

	string = self.request.body.decode("utf-8")

	if debug: print(string)
       
        try:
	   data = json.loads(string)
        except:
           return

	lines = []
	for d in data:
	    gtime = int(d['time'])
	    host = d['host'].replace('.','_')
	   
	    if d['plugin_instance']:
		#pluginstring = d['plugin'] + "-" + d['plugin_instance']
		pluginstring = d['plugin'] + "." + d['plugin_instance']
	    else:
		pluginstring = d['plugin']

	    if d['type_instance']:
		typestring = d['type'] + "." + d['type_instance']
	    else:
		typestring = d['type']

	    t = dict((ord(char), u'_') for char in ' ,')
	    t.update(dict((ord(char), None) for char in '+()"'))
	    s = pluginstring + "." + typestring
	    superstring = s.translate(t)

	    for i, value in enumerate(d['values']):
		metric = "collectd." + host + "." + superstring
		if len(d['values']) > 1:
		    metric = metric + "." + d['dsnames'][i]
		line = "{0} {1} {2}".format(metric, value, gtime)
		line = line + "\n"
		lines.append(line)

	if len(lines) > 0:
	    lines.append('')

	if debug:
	   print("=========================")
	   print(lines)

	try:
	    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	    sock.connect((ghost, gport))
	    connected = True
	except:
	    connected = False
	    print('Failed: no connection to db backend')

	if connected:
	    try:
		for l in lines:               
		    sock.sendall(l.encode())
		sock.close()
	    except socket.error as e:
		connected = False
		if isinstance(e.args, tuple):
		    output = 'Failed: socket error %d' % e[0]
		else:
		    output = 'Failed: socket error'
		print(output)

if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(
        handlers=[
            (r"/put/", PutHandler)
        ]
    )

    if options.https == "yes":
       if not os.path.isfile(options.ssl_cert) or not os.path.isfile(options.ssl_key):
          print("ERROR: cert/key file not available")
          sys.exit(1)

       ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
       ssl_ctx.load_cert_chain(options.ssl_cert, options.ssl_key)

       http_server = tornado.httpserver.HTTPServer(app, ssl_options=ssl_ctx)
    else:
       http_server = tornado.httpserver.HTTPServer(app)

    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
