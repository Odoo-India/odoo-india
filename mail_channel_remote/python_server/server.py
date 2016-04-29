# -*- coding: utf-8 -*-

import json
import requests
import urllib

from BaseHTTPServer import BaseHTTPRequestHandler
# from urlparse import urlparse, parse_qsl

# http://api.giphy.com/v1/gifs/search?q=cricket&api_key=dc6zaTOxFJmzC?limit=5
BASE_URL = 'http://api.giphy.com/v1/gifs/search?q='
command = ''
api_key = 'dc6zaTOxFJmzC'
# limit = '1'


class GetHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        post_body = {}
        if self.headers.get('command'):
            command = self.headers['command']
        REQUEST_URL = '%s?%s&api_key=%s' % (BASE_URL, command, api_key)
        if self.headers:
            post_body["token"] = self.headers.get('token')
        image = json.loads(urllib.urlopen(REQUEST_URL).read())
        if ('data' in image.keys()) and (len((image['data'])) > 0):
            img = image['data'][0]['images']['fixed_height_small_still']['url']
            post_body['image'] = img
        else:
            post_body["message"] = "Oops!!! sorry, image not found :("
        body = json.dumps(post_body)
        data = json.loads(body)
        requests.post(self.path[2:], data=data)
        self.send_response(200)
        self.end_headers()
        return

    def do_POST(self):
        post_body = {}
        if self.headers.get('command'):
            command = self.headers['command']
        REQUEST_URL = '%s?%s&api_key=%s' % (BASE_URL, command, api_key)
        if self.headers:
            post_body["token"] = self.headers.get('token')
        image = json.loads(urllib.urlopen(REQUEST_URL).read())
        if ('data' in image.keys()) and (len((image['data'])) > 0):
            img = image['data'][0]['images']['fixed_height_small_still']['url']
            post_body['image'] = img
        else:
            post_body["message"] = "Oops!!! sorry, image not found :("
        body = json.dumps(post_body)
        data = json.loads(body)
        requests.post(self.path[2:], data=data)
        self.send_response(200)
        self.end_headers()
        return


if __name__ == '__main__':
    from BaseHTTPServer import HTTPServer
    server = HTTPServer(('localhost', 9000), GetHandler)
    print "Starting server, use <Ctrl-C> to stop"
    server.serve_forever()
