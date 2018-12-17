import os
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer


class base_case(object):
    '''Parent for case handlers.'''

    def handle_file(self, handler, full_path):
        try:
            with open(full_path, 'rb') as reader:
                content = reader.read()
            handler.send_content(content)
        except IOError as msg:
            msg = "'{0}' cannot be read: {1}".format(full_path, msg)
            handler.handle_error(msg)

    def index_path(self, handler):
        return os.path.join(handler.full_path, "index.html")

    def test(self, handler):
        assert False, 'Not implemented'

    def act(self, handler):
        assert False, 'Not implemented'


class case_cgi_file(base_case):
    def test(self, handler):
        return os.path.isfile(handler.full_path) and \
                handler.full_path.endswith('.py')

    def act(self, handler):
        handler.run_cgi(handler.full_path)


class case_no_file(base_case):
    '''case file is not exists'''

    def test(self, handler):
        return not os.path.exists(handler.full_path)

    def act(self, handler):
        raise ServerException("'{0}' not found".format(handler.path))


class case_existing_file(base_case):
    '''case file is exists'''

    def test(self, handler):
        return os.path.isfile(handler.full_path)

    def act(self, handler):
        self.handle_file(handler, handler.full_path)


class case_always_fail(base_case):
    def test(self, handler):
        return True

    def act(self, handler):
        raise ServerException("Unknown object '{0}'".format(handler.path))


class case_directory_index_file(base_case):
    '''Serve index.html page for a directory.'''

    def test(self, hander):
        return os.path.isdir(hander.full_path) and \
                os.path.isfile(self.index_path(hander))

    def act(self, handler):
        self.handle_file(handler, self.index_path(handler))


class case_directory_no_index_file(base_case):
    def test(self, handler):
        return os.path.isdir(handler.full_path) and \
               not os.path.isfile(self.index_path(handler))

    def act(self, handler):
        handler.list_dir(handler.full_path)


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

    List_Page = ''' \
    <html>
        <body>
            <ul>
            {0}
            </ul>
        </body>
    </html>
    '''

    def run_cgi(self, full_path):
        cmd = 'python ' + full_path
        out = subprocess.Popen(
            cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        out.stdin.close()
        data = out.stdout.read()
        out.stdout.close()
        self.send_content(data)

    def list_dir(self, full_path):
        try:
            entries = os.listdir(full_path)
            bullets = [
                '<li>{0}</li>'.format(e) for e in entries
                if not e.startswith('.')
            ]
            page = self.List_Page.format('\n'.join(bullets)).encode()
            self.send_content(page)
        except OSError as msg:
            self.handle_error(msg)

    def handle_error(self, msg):
        content = self.Error_Page.format(path=self.path, msg=msg).encode()
        self.send_content(content, 404)

    def send_content(self, content, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    Cases = [
        case_no_file, case_cgi_file, case_existing_file,
        case_directory_index_file, case_directory_no_index_file,
        case_always_fail
    ]

    # Handle a Get request.

    def do_GET(self):
        # self.send_page(self.create_page())
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
