#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.request
~~~~~~~~~~~~~~~~~

This module provides a Request object to manage and persist 
request settings (cookies, auth, proxies).
"""
from .dictionary import CaseInsensitiveDict

class Request():
    """The fully mutable "class" `Request <Request>` object,
    containing the exact bytes that will be sent to the server.

    Instances are generated from a "class" `Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.

    Usage::

      >>> import deamon.request
      >>> req = request.Request()
      ## Incoming message obtain aka. incoming_msg
      >>> r = req.prepare(incoming_msg)
      >>> r
      <Request>
    """
    __attrs__ = [
        "method",
        "url",
        "headers",
        "body",
        "reason",
        "cookies",
        "routes",
        "hook",
        "version",
    ]

    def __init__(self):
        #: HTTP verb to send to the server.
        self.method = None
        #: HTTP URL to send the request to.
        self.url = None
        #: dictionary of HTTP headers.
        self.headers = None
        #: HTTP path
        self.path = None
        #: HTTP version
        self.version = None
        # The cookies set used to create Cookie header
        self.cookies = None
        #: request body to send to the server.
        self.body = None
        #: Routes
        self.routes = {}
        #: Hook point for routed mapped-path
        self.hook = None

    def extract_request_line(self, request):
        """
        Extract method, path, and version from the HTTP request line.

        :param request (str): Raw HTTP request.
        :return (tuple): (method, path, version) or (None, None, None) on error.
        """
        try:
            lines = request.splitlines()
            if not lines:
                return None, None, None
            
            first_line = lines[0]
            parts = first_line.split()
            
            if len(parts) != 3:
                return None, None, None
            
            method, path, version = parts

            # Default to index.html if root path
            if path == '/':
                path = '/index.html'
            
            return method, path, version
        except Exception as e:
            print(f"[Request] Error parsing request line: {e}")
            return None, None, None
             
    def prepare_headers(self, request):
        """
        Prepares the given HTTP headers.

        :param request (str): Raw HTTP request.
        :return (dict): Dictionary of headers (lowercase keys).
        """
        lines = request.split('\r\n')
        headers = {}
        
        for line in lines[1:]:
            if ': ' in line:
                key, val = line.split(': ', 1)
                headers[key.lower()] = val
        
        return headers

    def prepare_body(self, request):
        """
        Extract the body from the HTTP request.

        :param request (str): Raw HTTP request.
        :return (str): Request body or empty string.
        """
        # Body is after the blank line (\r\n\r\n)
        parts = request.split('\r\n\r\n', 1)
        if len(parts) == 2:
            return parts[1]
        return ''

    def prepare_cookies(self, headers):
        """
        Parse cookies from the Cookie header.

        :param headers (dict): Request headers.
        :return (dict): Dictionary of cookies.
        """
        cookies = {}
        cookie_header = headers.get('cookie', '')
        
        if cookie_header:
            # Parse: "name1=value1; name2=value2"
            for pair in cookie_header.split(';'):
                pair = pair.strip()
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    cookies[key.strip()] = value.strip()
        
        return cookies

    def prepare(self, request, routes=None):
        """
        Prepares the entire request with the given parameters.

        :param request (str): Raw HTTP request.
        :param routes (dict): Route mappings for RESTful endpoints.
        """

        # Prepare the request line from the request header
        self.method, self.path, self.version = self.extract_request_line(request)
        
        if self.method is None:
            print("[Request] Invalid request format")
            return
        
        print("[Request] {} path {} version {}".format(self.method, self.path, self.version))

        # Prepare headers
        self.headers = self.prepare_headers(request)
        
        # Prepare body (for POST/PUT requests)
        self.body = self.prepare_body(request)
        
        # Prepare cookies from headers
        self.cookies = self.prepare_cookies(self.headers)
        
        if self.cookies:
            print("[Request] Cookies received: {}".format(self.cookies))

        # Prepare the webapp hook with WeApRous instance
        # The default behaviour with HTTP server is empty routed
        if routes and routes != {}:
            self.routes = routes
            
            # Look for hook matching (method, path)
            self.hook = routes.get((self.method, self.path))
            
            if self.hook:
                print("[Request] Found route hook for {} {}".format(self.method, self.path))

        return

    def prepare_content_length(self, body):
        """
        Set Content-Length header based on body.

        :param body (str): Request body.
        """
        if body:
            if not self.headers:
                self.headers = {}
            self.headers["Content-Length"] = str(len(body))
        else:
            if not self.headers:
                self.headers = {}
            self.headers["Content-Length"] = "0"

    def prepare_auth(self, auth, url=""):
        """
        Prepare request authentication.

        :param auth (tuple): (username, password) tuple.
        :param url (str): Request URL.
        """
        # TODO: implement authentication
        # For now, store auth info
        if auth:
            username, password = auth
            # Could implement Basic Auth encoding here
            # import base64
            # credentials = f"{username}:{password}"
            # encoded = base64.b64encode(credentials.encode()).decode()
            # self.headers['Authorization'] = f'Basic {encoded}'
        return