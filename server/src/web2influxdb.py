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
import json
from datetime import datetime
from influxdb_client import InfluxDBClient

from tornado.options import define, options
define("port", default=8000, help="run on the given port", type=int)
define("https", default="yes", help="enable http with SSL")
define("auth_user", default="admin", help="authentication username")
define("auth_pass", default="4dm1n", help="authentication password")
define("ssl_cert", default="ssl-cert.crt", help="SSL certificate file")
define("ssl_key", default="ssl-key.key", help="SSL key file")

debug = True
write_api = None

# base collectd metric format
# host "." plugin ["-" plugin instance] "/" type ["-" type instance]

class PutHandler(tornado.web.RequestHandler):

    def prepare(self):
        auth_header = self.request.headers.get('Authorization')
        if auth_header is None: 
            if debug: 
                print("no auth header")
            self.set_status(401)
            self.set_header('WWW-Authenticate', 'Basic realm=Users')
            return
        if not auth_header.startswith('Basic '): 
            if debug: 
                print("no basic auth method")
            self.set_status(401)
            self.set_header('WWW-Authenticate', 'Basic realm=Users')
            return

        auth_decoded = base64.decodebytes(auth_header[6:].encode()).decode()
        username, password = auth_decoded.split(':', 2)

        if username != options.auth_user or password != options.auth_pass:
           print("auth fail")
           return

        print("auth ok")

    def post(self):
        string = self.request.body.decode("utf-8")
        
        try:
            data = json.loads(string)
        except:
            return

        lines = []
        for d in data:
            host = d['host'].replace('.','_')

            for i, v in enumerate(d['dsnames']):
                if d['plugin'] == d['type']:
                    measurement = f"{d['plugin']}"
                else: 
                    measurement = f"{d['plugin']}.{d['type']}"
                if d['type_instance']:
                    measurement = f"{measurement}.{d['type_instance']}"
                resource = d['plugin_instance'] if d['plugin_instance'] else d['plugin']

                if d['dsnames'][i] != 'value':
                    measurement = f"{measurement}.{d['dsnames'][i]}"

                if d['values'][i] != -999:
                    lines.append({
                        "measurement": measurement,
                        "tags": {"host": host, "resource": resource},
                        "fields": {"value": d['values'][i]},
                        "time": int(d['time'])
                    })
        
        if debug:
            for line in lines:
                print(datetime.fromtimestamp(line['time']), line)

        try:
            write_api.write("graphite", "INFN", lines)
        except:
            print('Failed: no connection to db backend')

        
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

    client = InfluxDBClient(url="http://localhost:8086", token="", org="INFN")
    write_api = client.write_api()

    http_server.listen(options.port)
    try:
        tornado.ioloop.IOLoop.instance().start()
    except:
        write_api.flush()
        write_api.close()
        client.close()
        print("Bye!")
