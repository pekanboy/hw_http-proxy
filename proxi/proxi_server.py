import os
import socket
import time
from urllib.parse import urlparse


class ProxiServer:
    def __init__(self, host='127.0.0.1', port=5000):
        self._port = port
        self._host = host

        self._socket = socket.socket()
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((host, port))

        self._active_children = set()

    def start_listen(self):
        self._socket.listen()
        print(f'Server started on http://{self._host}:{self._port}...')

        timing = time.time()

        try:
            while True:
                pid = self.start_handling()
                print('connect...', pid)
                self._active_children.add(pid)

                if time.time() - timing > 10.0:
                    timing = time.time()
                    self.reap_children(self._active_children)
        except Exception as err:
            print(str(err.args))

    def start_handling(self):
        conn, _ = self._socket.accept()

        children_pid = os.fork()

        if children_pid:
            conn.close()
            return children_pid

        data = self.get_data(conn)

        request, host, port = self.format_data(data.decode())

        response = self.send_data(request, host, port)

        conn.send(response)

        conn.close()
        os._exit(0)

    def get_data(self, conn):
        data = conn.recv(4056)
        return data

    def format_data(self, data: str):
        raw_url = data.split(' ')[1]
        url = urlparse(raw_url)

        data = data.replace(raw_url, url.path, 1)

        result = []

        for row in data.split('\r\n'):
            if row.upper().startswith('Proxy-Connection:'.upper()):
                continue
            result.append(row)

        return '\r\n'.join(result), url.hostname, url.port if url.port else 80

    def send_data(self, request, host, port):
        sock = socket.socket()
        sock.connect((host, port))
        sock.send(request.encode('utf-8'))

        response = self.get_data(sock)

        sock.close()

        return response

    def reap_children(self, active_children):
        for child_pid in active_children.copy():
            child_pid, _ = os.waitpid(child_pid, os.WNOHANG)
            if child_pid:
                active_children.discard(child_pid)


