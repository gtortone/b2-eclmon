#!/usr/bin/env python3

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import json, socket

from tornado.options import define, options
define("port", default=8000, help="run on the given port", type=int)

debug = False
ghost = "localhost"	# modify here
gport = 2003

# base collectd metric format
# host "." plugin ["-" plugin instance] "/" type ["-" type instance]

class PutHandler(tornado.web.RequestHandler):
    def post(self):
        string = self.request.body.decode("utf-8")

        #print(string)

        data = json.loads(string)

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
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
