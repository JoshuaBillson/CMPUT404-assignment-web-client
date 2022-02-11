#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib.parse


class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

    def __str__(self):
        return self.body


class HTTPClient(object):
    def __init__(self):
        self.host = None
        self.port = None
        self.action = None
        self.socket = None
        self.path = None
        self.headers = None

    def get_host_port(self, url, port=80):
        p = urllib.parse.urlparse(url if url[0:7] == "http://" else "http://" + url, scheme='http')
        self.host = p.hostname
        self.path = p.path if p.path else "/"
        self.port = p.port if p.port else port

    def connect(self, url, port=80):
        self.get_host_port(url, port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        return None

    @staticmethod
    def get_code(response):
        return re.search("HTTP/1.\d (\d+) .+", response.split("\r\n")[0]).group(1)

    @staticmethod
    def get_body(response):
        return response.split("\r\n\r\n")[1]

    def sendall(self, data):
        self.socket.sendall(data.encode('utf-8'))

    def close(self):
        self.socket.close()

    # read everything from the socket
    def recvall(self):
        buffer = bytearray()
        done = False
        while not done:
            part = self.socket.recv(1024)
            buffer += part
            done = part == b''
        try:
            return buffer.decode('utf-8')
        except UnicodeDecodeError:
            return buffer.decode('ISO-8859-1')

    def GET(self, url, port=80, args=None):
        # Open Connection
        self.connect(url, port)

        # Create Query String
        query_string = ("?" + "&".join([f"{key}={value}" for key, value in args.items()])) if args else ""

        # Create Request
        lines = [f"GET {self.path + query_string} HTTP/1.1",
                 f"Host: {self.host}",
                 f"User-Agent: Python",
                 f"Connection: close",
                 f"Accept: */*\r\n\r\n"
                 ]
        request = "\r\n".join(lines)

        # Send Request
        return self.send_request(request)

    def POST(self, url, port=80, args=None):
        # Open Connection
        self.connect(url, port)

        # Create Body
        body = [f"{key}={value}" for key, value in args.items()] if args else []
        body = "&".join(body)

        # Create Request
        lines = [f"POST {self.path} HTTP/1.1",
                 f"Host: {self.host}",
                 f"User-Agent: Python",
                 f"Content-Type: application/x-www-form-urlencoded",
                 f"Connection: close",
                 f"Accept: */*",
                 f"Content-Length: {len(body.encode('utf-8'))}",
                 f"\r\n{body}"
                 ]
        request = "\r\n".join(lines)

        # Send Request
        return self.send_request(request)

    def send_request(self, request):
        self.sendall(request)
        response = self.recvall()
        self.close()
        return self.parse_response(response)

    def parse_response(self, response):
        code = self.get_code(response)
        body = self.get_body(response)
        return HTTPResponse(code=int(code), body=body)

    def command(self, url, command="GET", args=None):
        if command == "POST":
            return self.POST(url, args=args)
        return self.GET(url, args=args)


if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if len(sys.argv) <= 1:
        print("httpclient.py [GET/POST] [URL]\n")
        sys.exit(1)
    elif len(sys.argv) == 3:
        print(client.command(sys.argv[2], sys.argv[1]))
    elif len(sys.argv) > 3:
        args = dict()
        for arg in sys.argv[3:]:
            k, v = arg.split("=")
            args[k] = v
        print(client.command(sys.argv[2], sys.argv[1], args=args))

    else:
        print(client.command(sys.argv[1]))
