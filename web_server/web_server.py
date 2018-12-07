#!/usr/bin/env python

from http.server import HTTPServer, BaseHTTPRequestHandler
import os

class ServerException(Exception):
    '''Server inner error'''
    pass

class RequestHandler(BaseHTTPRequestHandler):
    '''Handle HTTP request by returning a fixed 'page'.'''

    Error_Page = '''\
    <html>
        <body>
            <h1>Error accessing {path}</h1>
            <p>{msg}</p>
        </body>
    </html>
    '''
    
    def handle_error(self, msg):
        content = self.Error_Page.format(path = self.path, msg=msg)
        self.send_content(content, 404)

    def handle_file(self, full_path):
        try:
            with open(full_path, 'r') as reader:
                contant = reader.read()
            self.send_content(contant)
        except IOError as msg:
            msg = "'{0}' cannot be read:{1}".format(self.path, msg)
            self.handle_error(msg)

    def send_content(self, content, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-Length',str(len(content)))
        self.end_headers()
        self.wfile.write(content.encode())

    #Handle a Get request.
    def do_GET(self):
        #self.send_page(self.create_page())
        try:
            # Figure out what exactly is being requested.
            full_path = os.getcwd() + self.path

            # If dosn't exist...
            if not os.path.exists(full_path):
                raise ServerException("'{0}' not found".format(self.path))

            elif os.path.isfile(full_path):
                self.handle_file(full_path)
            
            else:
                raise ServerException("Unknow object '{0}'".format(self.path))
        except Exception as msg:
            self.handle_error(msg)


if __name__ == '__main__':
    serverAddress = ('localhost', 8080)
    server = HTTPServer(serverAddress, RequestHandler)
    print("Starting server, listen at : %s:%s" % serverAddress)
    server.serve_forever()