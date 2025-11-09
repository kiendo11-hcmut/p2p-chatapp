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
daemon.httpadapter
~~~~~~~~~~~~~~~~~

This module provides a http adapter object to manage and persist 
http settings (headers, bodies). The adapter supports both
raw URL paths and RESTful route definitions, and integrates with
Request and Response objects to handle client-server communication.
"""

from .request import Request
from .response import Response
from .dictionary import CaseInsensitiveDict

class HttpAdapter:
    """
    A mutable :class:`HTTP adapter <HTTP adapter>` for managing client connections
    and routing requests.

    The `HttpAdapter` class encapsulates the logic for receiving HTTP requests,
    dispatching them to appropriate route handlers, and constructing responses.
    It supports RESTful routing via hooks and integrates with :class:`Request <Request>` 
    and :class:`Response <Response>` objects for full request lifecycle management.

    Attributes:
        ip (str): IP address of the client.
        port (int): Port number of the client.
        conn (socket): Active socket connection.
        connaddr (tuple): Address of the connected client.
        routes (dict): Mapping of route paths to handler functions.
        request (Request): Request object for parsing incoming data.
        response (Response): Response object for building and sending replies.
    """

    __attrs__ = [
        "ip",
        "port",
        "conn",
        "connaddr",
        "routes",
        "request",
        "response",
    ]

    def __init__(self, ip, port, conn, connaddr, routes):
        """
        Initialize a new HttpAdapter instance.

        :param ip (str): IP address of the client.
        :param port (int): Port number of the client.
        :param conn (socket): Active socket connection.
        :param connaddr (tuple): Address of the connected client.
        :param routes (dict): Mapping of route paths to handler functions.
        """

        #: IP address.
        self.ip = ip
        #: Port.
        self.port = port
        #: Connection
        self.conn = conn
        #: Conndection address
        self.connaddr = connaddr
        #: Routes
        self.routes = routes
        #: Request
        self.request = Request()
        #: Response
        self.response = Response()

    def handle_client(self, conn, addr, routes):
        print("[Server] Connected by", addr)
        try:
            data = conn.recv(4096)
            if not data:
                print("[Server] No data received from", addr)
                return

            msg = data.decode(errors='ignore')
            print("[DEBUG] Raw message:", msg)

            # Parse request
            req = Request()
            req.prepare(msg, routes)
            print(f"[Request] {req.method} path {req.path} version {req.version}")

            # 🔥 TRẢ VỀ RESPONSE ĐƠN GIẢN (test)
            html = "<html><body><h1>Server OK ✅</h1><p>You requested: {}</p></body></html>".format(req.path)
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/html; charset=utf-8\r\n"
                f"Content-Length: {len(html.encode())}\r\n"
                "Connection: close\r\n\r\n"
                + html
            )
            conn.sendall(response.encode())
            print("[Server] Sent response to", addr)

        except Exception as e:
            print("[Server] Error handling client:", e)
            # Optional: gửi lỗi cho client
            error_msg = "HTTP/1.1 500 Internal Server Error\r\nContent-Length: 0\r\n\r\n"
            try:
                conn.sendall(error_msg.encode())
            except:
                pass
        finally:
            conn.close()

    def extract_cookies_from_request(self, req):
        """
        Extract cookies from the request headers.

        :param req (Request): The request object.
        :return (dict): Dictionary of cookie key-value pairs.
        """
        cookies = {}
        cookie_header = req.headers.get('cookie', '')
        
        if cookie_header:
            # Parse cookie string: "name1=value1; name2=value2"
            for pair in cookie_header.split(';'):
                pair = pair.strip()
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    cookies[key.strip()] = value.strip()
        
        return cookies

    def check_auth_cookie(self, req):
        """
        Check if the request has a valid authentication cookie.

        :param req (Request): The request object.
        :return (bool): True if authenticated, False otherwise.
        """
        cookies = req.cookies or {}
        auth_value = cookies.get('auth', '')
        return auth_value == 'true'

    def handle_login(self, req, resp):
        """
        Handle POST /login request with authentication.

        :param req (Request): The request object.
        :param resp (Response): The response object.
        :return (bytes): HTTP response.
        """
        # Parse form data from request body
        body = req.body or ''
        params = self.parse_form_data(body)
        
        username = params.get('username', '')
        password = params.get('password', '')
        
        print(f"[HttpAdapter] Login attempt - username: {username}")
        
        # Validate credentials (admin/password as per assignment)
        if username == 'admin' and password == 'password':
            # Success - load index page and set cookie
            try:
                with open('www/index.html', 'rb') as f:
                    content = f.read()
                
                # Build response with Set-Cookie header
                response = b"HTTP/1.1 200 OK\r\n"
                response += b"Content-Type: text/html\r\n"
                response += b"Set-Cookie: auth=true\r\n"  # Set authentication cookie
                response += f"Content-Length: {len(content)}\r\n".encode('utf-8')
                response += b"Connection: close\r\n"
                response += b"\r\n"
                response += content
                
                print("[HttpAdapter] Login successful - cookie set")
                return response
            except FileNotFoundError:
                # If index.html not found, return simple success message
                success_html = b"""<!DOCTYPE html>
<html>
<head><title>Login Success</title></head>
<body>
    <h2>Login Successful!</h2>
    <p>Welcome, admin!</p>
    <p><a href="/">Go to Homepage</a></p>
</body>
</html>"""
                response = b"HTTP/1.1 200 OK\r\n"
                response += b"Content-Type: text/html\r\n"
                response += b"Set-Cookie: auth=true\r\n"
                response += f"Content-Length: {len(success_html)}\r\n".encode('utf-8')
                response += b"Connection: close\r\n"
                response += b"\r\n"
                response += success_html
                return response
        else:
            # Failed - return 401 with login form
            print("[HttpAdapter] Login failed - invalid credentials")
            return self.build_login_page(error=True)

    def parse_form_data(self, body):
        """
        Parse URL-encoded form data.

        :param body (str): Request body containing form data.
        :return (dict): Dictionary of form parameters.
        """
        params = {}
        if body:
            for pair in body.split('&'):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    # URL decode if needed (basic implementation)
                    params[key] = value.replace('+', ' ')
        return params

    def build_login_page(self, error=False):
        """
        Build a 401 Unauthorized response with login form.

        :param error (bool): Whether to show error message.
        :return (bytes): HTTP response with login form.
        """
        error_msg = ""
        if error:
            error_msg = '<p style="color: red; font-weight: bold;">Invalid username or password!</p>'
        
        login_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Login Required</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 400px;
            margin: 100px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .login-box {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h2 {{
            color: #333;
            margin-bottom: 10px;
        }}
        input {{
            width: 100%;
            padding: 12px;
            margin: 8px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }}
        button {{
            width: 100%;
            padding: 12px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 10px;
        }}
        button:hover {{
            background-color: #0056b3;
        }}
        .hint {{
            color: #666;
            font-size: 12px;
            margin-top: 15px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="login-box">
        <h2>Login Required</h2>
        {error_msg}
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Username" required autofocus>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <p class="hint">Hint: admin / password</p>
    </div>
</body>
</html>"""
        
        response = b"HTTP/1.1 401 Unauthorized\r\n"
        response += b"Content-Type: text/html; charset=utf-8\r\n"
        response += f"Content-Length: {len(login_html.encode('utf-8'))}\r\n".encode('utf-8')
        response += b"Connection: close\r\n"
        response += b"\r\n"
        response += login_html.encode('utf-8')
        
        return response

    def build_hook_response(self, result):
        """
        Build HTTP response from hook result (for RESTful routes).

        :param result (str): Result from route handler.
        :return (bytes): HTTP response.
        """
        if result is None:
            result = '{"status": "success"}'
        
        content = str(result).encode('utf-8')
        
        response = b"HTTP/1.1 200 OK\r\n"
        response += b"Content-Type: application/json\r\n"
        response += f"Content-Length: {len(content)}\r\n".encode('utf-8')
        response += b"Connection: close\r\n"
        response += b"\r\n"
        response += content
        
        return response

    @property
    def extract_cookies(self):
        """
        Property to extract cookies (for backward compatibility).
        
        :rtype (dict): Dictionary of cookies.
        """
        return {}

    def build_response(self, req, resp):
        """Builds a :class:`Response <Response>` object 

        :param req: The :class:`Request <Request>` used to generate the response.
        :param resp: The response object.
        :rtype: Response
        """
        response = Response()

        # Set encoding.
        response.encoding = 'utf-8'
        response.raw = resp

        if isinstance(req.url, bytes):
            response.url = req.url.decode("utf-8")
        else:
            response.url = req.url

        # Add cookies from the request.
        response.cookies = req.cookies or {}

        # Give the Response some context.
        response.request = req
        response.connection = self

        return response

    def add_headers(self, request):
        """
        Add headers to the request.

        This method is intended to be overridden by subclasses to inject
        custom headers. It does nothing by default.

        :param request: :class:`Request <Request>` to add headers to.
        """
        pass

    def build_proxy_headers(self, proxy):
        """Returns a dictionary of the headers to add to any request sent
        through a proxy. 

        :class:`HttpAdapter <HttpAdapter>`.

        :param proxy: The url of the proxy being used for this request.
        :rtype: dict
        """
        headers = {}
        #
        # TODO: build your authentication here
        #       username, password =...
        # we provide dummy auth here
        #
        username, password = ("user1", "password")

        if username:
            headers["Proxy-Authorization"] = (username, password)

        return headers