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
daemon.response
~~~~~~~~~~~~~~~~~

This module provides a :class: `Response <Response>` object to manage and persist 
response settings (cookies, auth, proxies), and to construct HTTP responses
based on incoming requests. 

The current version supports MIME type detection, content loading and header formatting
"""
import datetime
import os
import mimetypes
from .dictionary import CaseInsensitiveDict

BASE_DIR = ""

class Response():   
    """The :class:`Response <Response>` object, which contains a
    server's response to an HTTP request.

    Instances are generated from a :class:`Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.

    :class:`Response <Response>` object encapsulates headers, content, 
    status code, cookies, and metadata related to the request-response cycle.
    It is used to construct and serve HTTP responses in a custom web server.

    :attrs status_code (int): HTTP status code (e.g., 200, 404).
    :attrs headers (dict): dictionary of response headers.
    :attrs url (str): url of the response.
    :attrsencoding (str): encoding used for decoding response content.
    :attrs history (list): list of previous Response objects (for redirects).
    :attrs reason (str): textual reason for the status code (e.g., "OK", "Not Found").
    :attrs cookies (CaseInsensitiveDict): response cookies.
    :attrs elapsed (datetime.timedelta): time taken to complete the request.
    :attrs request (PreparedRequest): the original request object.

    Usage::

      >>> import Response
      >>> resp = Response()
      >>> resp.build_response(req)
      >>> resp
      <Response>
    """

    __attrs__ = [
        "_content",
        "_header",
        "status_code",
        "method",
        "headers",
        "url",
        "history",
        "encoding",
        "reason",
        "cookies",
        "elapsed",
        "request",
        "body",
    ]


    def __init__(self, request=None):
        """
        Initializes a new :class:`Response <Response>` object.

        : params request : The originating request object.
        """

        self._content = b''
        self._content_consumed = False
        self._next = None

        #: Integer Code of responded HTTP Status, e.g. 404 or 200.
        self.status_code = None

        #: Case-insensitive Dictionary of Response Headers.
        #: For example, ``headers['content-type']`` will return the
        #: value of a ``'Content-Type'`` response header.
        self.headers = {}

        #: URL location of Response.
        self.url = None

        #: Encoding to decode with when accessing response text.
        self.encoding = None

        #: A list of :class:`Response <Response>` objects from
        #: the history of the Request.
        self.history = []

        #: Textual reason of responded HTTP Status, e.g. "Not Found" or "OK".
        self.reason = None

        #: A of Cookies the response headers.
        self.cookies = CaseInsensitiveDict()

        #: The amount of time elapsed between sending the request
        self.elapsed = datetime.timedelta(0)

        #: The :class:`PreparedRequest <PreparedRequest>` object to which this
        #: is a response.
        self.request = None


    def get_mime_type(self, path):
        """
        Determines the MIME type of a file based on its path.

        "params path (str): Path to the file.

        :rtype str: MIME type string (e.g., 'text/html', 'image/png').
        """

        try:
            mime_type, _ = mimetypes.guess_type(path)
        except Exception:
            return 'application/octet-stream'
        return mime_type or 'application/octet-stream'


    def prepare_content_type(self, mime_type='text/html'):
        """
        Prepares the Content-Type header and determines the base directory
        for serving the file based on its MIME type.

        :params mime_type (str): MIME type of the requested resource.

        :rtype str: Base directory path for locating the resource.

        :raises ValueError: If the MIME type is unsupported.
        """
        
        base_dir = ""

        # Processing mime_type based on main_type and sub_type
        main_type, sub_type = mime_type.split('/', 1)
        print("[Response] processing MIME main_type={} sub_type={}".format(main_type, sub_type))
        
        if main_type == 'text':
            self.headers['Content-Type'] = 'text/{}'.format(sub_type)
            if sub_type == 'plain' or sub_type == 'css':
                base_dir = BASE_DIR + "static/"
            elif sub_type == 'html':
                base_dir = BASE_DIR + "www/"
            else:
                # Handle other text types
                base_dir = BASE_DIR + "static/"
        elif main_type == 'image':
            base_dir = BASE_DIR + "static/images/"
            self.headers['Content-Type'] = 'image/{}'.format(sub_type)
        elif main_type == 'application':
            base_dir = BASE_DIR + "apps/"
            self.headers['Content-Type'] = 'application/{}'.format(sub_type)
        #
        # TODO: process other mime_type
        #       application/xml, application/zip
        #       text/csv, text/xml
        #       video/mp4, video/mpeg
        #
        else:
            raise ValueError("Invalid MIME type: main_type={} sub_type={}".format(main_type, sub_type))

        return base_dir


    def build_content(self, path, base_dir):
        """
        Loads the objects file from storage space.

        :params path (str): relative path to the file.
        :params base_dir (str): base directory where the file is located.

        :rtype tuple: (int, bytes) representing content length and content data.
        """

        filepath = os.path.join(base_dir, path.lstrip('/'))

        print("[Response] serving the object at location {}".format(filepath))
        
        try:
            # Read file content
            with open(filepath, 'rb') as f:
                content = f.read()
            
            return len(content), content
        except FileNotFoundError:
            print("[Response] File not found: {}".format(filepath))
            # Return empty content
            return 0, b''
        except Exception as e:
            print("[Response] Error reading file: {}".format(e))
            return 0, b''


    def set_cookie(self, name, value, max_age=None, path='/', http_only=False):
        """
        Set a cookie in the response.

        :param name (str): Cookie name.
        :param value (str): Cookie value.
        :param max_age (int): Optional max age in seconds.
        :param path (str): Cookie path (default: '/').
        :param http_only (bool): HttpOnly flag.
        """
        cookie_str = "{}={}; Path={}".format(name, value, path)
        
        if max_age:
            cookie_str += "; Max-Age={}".format(max_age)
        
        if http_only:
            cookie_str += "; HttpOnly"
        
        # Store in headers
        if 'Set-Cookie' in self.headers:
            # Multiple cookies - convert to list
            existing = self.headers['Set-Cookie']
            if isinstance(existing, list):
                existing.append(cookie_str)
            else:
                self.headers['Set-Cookie'] = [existing, cookie_str]
        else:
            self.headers['Set-Cookie'] = cookie_str
        
        print("[Response] Cookie set: {}".format(cookie_str))


    def build_response_header(self, request):
        """
        Constructs the HTTP response headers based on the class:`Request <Request>
        and internal attributes.

        :params request (class:`Request <Request>`): incoming request object.

        :rtypes bytes: encoded HTTP response header.
        """
        reqhdr = request.headers
        rsphdr = self.headers

        # Build dynamic headers
        headers = {
            "Accept": "{}".format(reqhdr.get("accept", "application/json")),
            "Accept-Language": "{}".format(reqhdr.get("accept-language", "en-US,en;q=0.9")),
            "Cache-Control": "no-cache",
            "Content-Type": "{}".format(self.headers.get('Content-Type', 'text/html')),
            "Content-Length": "{}".format(len(self._content)),
            "Date": "{}".format(datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")),
            "Connection": "close",
        }

        # Add Set-Cookie header if present
        if 'Set-Cookie' in self.headers:
            headers['Set-Cookie'] = self.headers['Set-Cookie']

        # Header text alignment - format as HTTP response
        fmt_header = "HTTP/1.1 200 OK\r\n"
        
        for key, value in headers.items():
            if key == 'Set-Cookie' and isinstance(value, list):
                # Multiple cookies
                for cookie in value:
                    fmt_header += "Set-Cookie: {}\r\n".format(cookie)
            else:
                fmt_header += "{}: {}\r\n".format(key, value)
        
        fmt_header += "\r\n"  # Empty line between headers and body

        return fmt_header.encode('utf-8')


    def build_notfound(self):
        """
        Constructs a standard 404 Not Found HTTP response.

        :rtype bytes: Encoded 404 response.
        """

        html_content = """<!DOCTYPE html>
<html>
<head>
    <title>404 Not Found</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #d9534f;
            font-size: 72px;
            margin: 0;
        }
        p {
            font-size: 24px;
            color: #333;
        }
    </style>
</head>
<body>
    <h1>404</h1>
    <p>Page Not Found</p>
    <p><a href="/">Go to Homepage</a></p>
</body>
</html>"""

        return (
            "HTTP/1.1 404 Not Found\r\n"
            "Content-Type: text/html\r\n"
            "Content-Length: {}\r\n"
            "Connection: close\r\n"
            "\r\n"
            "{}".format(len(html_content), html_content)
        ).encode('utf-8')


    def build_response(self, request):
        """
        Builds a full HTTP response including headers and content based on the request.

        :params request (class:`Request <Request>`): incoming request object.

        :rtype bytes: complete HTTP response using prepared headers and content.
        """

        path = request.path

        mime_type = self.get_mime_type(path)
        print("[Response] {} path {} mime_type {}".format(request.method, request.path, mime_type))

        base_dir = ""

        # Determine base directory based on MIME type
        if path.endswith('.html') or mime_type == 'text/html':
            base_dir = self.prepare_content_type(mime_type='text/html')
        elif mime_type == 'text/css':
            base_dir = self.prepare_content_type(mime_type='text/css')
        elif mime_type.startswith('image/'):
            base_dir = self.prepare_content_type(mime_type=mime_type)
        elif mime_type == 'application/javascript' or mime_type == 'text/javascript':
            base_dir = BASE_DIR + "static/js/"
            self.headers['Content-Type'] = 'application/javascript'
        #
        # TODO: add support for more objects (JSON, XML, etc.)
        #
        else:
            print("[Response] Unsupported MIME type: {}".format(mime_type))
            return self.build_notfound()

        # Load content
        c_len, self._content = self.build_content(path, base_dir)
        
        if c_len == 0:
            # File not found
            return self.build_notfound()

        # Build headers
        self._header = self.build_response_header(request)

        # Return complete response
        return self._header + self._content