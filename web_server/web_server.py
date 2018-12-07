#!/usr/bin/env python

from http.server import HTTPServer, BaseHTTPRequestHandler
import os

class case_no_file(object):
    '''case file is not exists'''
    def test(self, handler):
        return not os.path.exists(handler.full_path)
    
    def act(self, handler):
        raise ServerException("'{0}' not found".format(handler.path))

class case_existing_file(object):
    '''case file is exists'''
    def test(self, handler):
        return os.path.isfile(handler.full_path)
    
    def act(self, handler):
        handler.handle_file(handler.full_path)

class case_always_fail(object):
    def test(self, handler):
        return True
    
    def act(self, handler):
        raise ServerException("Unknown object '{0}'".format(handler.path))
        

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

    Cases = [case_no_file, case_existing_file, case_always_fail]
    #Handle a Get request.
    def do_GET(self):
        #self.send_page(self.create_page())
        try:
            # Figure out what exactly is being requested.
            self.full_path = os.getcwd() + self.path

            for case in self.Cases:
                handler = case()
                if handler.test(self):
                    handler.act(self)
                    break
        except Exception as msg:
            self.handle_error(msg)


if __name__ == '__main__':
    serverAddress = ('localhost', 8080)
    server = HTTPServer(serverAddress, RequestHandler)
    print("Starting server, listen at : %s:%s" % serverAddress)
    server.serve_forever()