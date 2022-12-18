from datetime import datetime
import json
import mimetypes
import pathlib
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from threading import Thread


path_to_data_file = pathlib.Path('front-init/storage/data.json')
path_to_data_dir = pathlib.Path('front-init/storage')
front_path = pathlib.Path('front-init/pages')
IP = '127.0.0.1'
UDP_PORT = 5000
HTTP_PORT = 3000
dict_to_write = {}


def check_path():
    if path_to_data_file.exists():
        print('File ready to writing')
    else:
        if path_to_data_dir.exists():
            path_to_data_file.touch()
        else:
            path_to_data_dir.mkdir()
            path_to_data_file.touch()


class HTTPRequestHandler(BaseHTTPRequestHandler):
    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(pathlib.Path(front_path, filename), 'rb') as file:
            self.wfile.write(file.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        run_client(message=data)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()


def run_server(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    sock.bind(server)
    try:
        while True:
            data, address = sock.recvfrom(1024)
            print(f'SERVER: Received data: {data.decode()} from: {address}')
            data_parse = urllib.parse.unquote_plus(data.decode())
            data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
            print(data_dict)
            dict_to_write[str(datetime.now())] = data_dict
            with open('front-init/storage/data.json', 'w') as file:
                json.dump(dict_to_write, file, indent=4, separators=(',', ': '))
            sock.sendto(data, address)
            print(f'SERVER: Send data: {data.decode()} to: {address}')
    except KeyboardInterrupt:
        print(f'Destroy server')
    finally:
        sock.close()


def run_client(ip: str = IP, port: int = UDP_PORT, message: bytes = None):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        server = ip, port
        sock.sendto(message, server)
        print(f'CLIENT: Send data: {message.decode()} to server: {server}')
        response, address = sock.recvfrom(1024)
        print(f'CLIENT Response data: {response.decode()} from address: {address}')


def run():
    http = HTTPServer((IP, HTTP_PORT), HTTPRequestHandler)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


t1 = Thread(target=run)
t2 = Thread(target=run_server, args=(IP, UDP_PORT))

if __name__ == '__main__':
    check_path()
    t1.start()
    t2.start()
    t1.join()
    t2.join()
