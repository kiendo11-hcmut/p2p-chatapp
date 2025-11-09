"""
apps.chatapp
~~~~~~~~~~~~~~~~~
This module implements a chat web application using WeApRous framework.
It provides RESTful APIs for peer registration, channel management, and peer discovery.

This app acts as a web interface to the chat tracker server.
"""

import json
import socket
from daemon.weaprous import WeApRous


class ChatWebApp:
    """
    Web application for chat system using RESTful APIs.
    
    Provides endpoints for:
    - User login
    - Peer registration
    - Channel management
    - Peer discovery
    """
    
    def __init__(self, tracker_host='127.0.0.1', tracker_port=7000):
        """
        Initialize the chat web application.
        
        :param tracker_host (str): IP of the tracker server.
        :param tracker_port (int): Port of the tracker server.
        """
        self.tracker_host = tracker_host
        self.tracker_port = tracker_port
        self.app = WeApRous()
        self.setup_routes()
    
    def setup_routes(self):
        """Setup all RESTful routes for the chat application."""
        
        @self.app.route('/login', methods=['POST'])
        def login(headers="guest", body="anonymous"):
            """
            Handle user login.
            
            Expected body: {"username": "user1", "password": "pass123"}
            """
            try:
                data = json.loads(body) if body and body != "anonymous" else {}
                username = data.get('username', '')
                password = data.get('password', '')
                
                # Simple validation (in production, use proper authentication)
                if username and password:
                    response = {
                        'status': 'success',
                        'message': 'Login successful',
                        'username': username,
                        'token': f'token_{username}'  # Simplified token
                    }
                else:
                    response = {
                        'status': 'error',
                        'message': 'Invalid credentials'
                    }
                
                return json.dumps(response)
            except Exception as e:
                return json.dumps({
                    'status': 'error',
                    'message': str(e)
                })
        
        @self.app.route('/register-peer', methods=['POST'])
        def register_peer(headers="guest", body="anonymous"):
            """
            Register a peer with the tracker server.
            
            Expected body: {
                "peer_id": "uuid",
                "ip": "192.168.1.100",
                "port": 9001,
                "username": "user1"
            }
            """
            try:
                data = json.loads(body) if body and body != "anonymous" else {}
                
                # Forward request to tracker server
                response = self.send_to_tracker('register', data)
                return json.dumps(response)
            except Exception as e:
                return json.dumps({
                    'status': 'error',
                    'message': str(e)
                })
        
        @self.app.route('/get-peers', methods=['POST'])
        def get_peers(headers="guest", body="anonymous"):
            """
            Get list of active peers, optionally filtered by channel.
            
            Expected body: {
                "channel": "general"  (optional)
            }
            """
            try:
                data = json.loads(body) if body and body != "anonymous" else {}
                response = self.send_to_tracker('get_peers', data)
                return json.dumps(response)
            except Exception as e:
                return json.dumps({
                    'status': 'error',
                    'message': str(e)
                })
        
        @self.app.route('/join-channel', methods=['POST'])
        def join_channel(headers="guest", body="anonymous"):
            """
            Join a chat channel.
            
            Expected body: {
                "peer_id": "uuid",
                "channel": "general"
            }
            """
            try:
                data = json.loads(body) if body and body != "anonymous" else {}
                response = self.send_to_tracker('join_channel', data)
                return json.dumps(response)
            except Exception as e:
                return json.dumps({
                    'status': 'error',
                    'message': str(e)
                })
        
        @self.app.route('/leave-channel', methods=['POST'])
        def leave_channel(headers="guest", body="anonymous"):
            """
            Leave a chat channel.
            
            Expected body: {
                "peer_id": "uuid",
                "channel": "general"
            }
            """
            try:
                data = json.loads(body) if body and body != "anonymous" else {}
                response = self.send_to_tracker('leave_channel', data)
                return json.dumps(response)
            except Exception as e:
                return json.dumps({
                    'status': 'error',
                    'message': str(e)
                })
        
        @self.app.route('/get-channels', methods=['POST'])
        def get_channels(headers="guest", body="anonymous"):
            """
            Get list of channels a peer has joined.
            
            Expected body: {
                "peer_id": "uuid"
            }
            """
            try:
                data = json.loads(body) if body and body != "anonymous" else {}
                response = self.send_to_tracker('get_channels', data)
                return json.dumps(response)
            except Exception as e:
                return json.dumps({
                    'status': 'error',
                    'message': str(e)
                })
        
        @self.app.route('/logout', methods=['POST'])
        def logout(headers="guest", body="anonymous"):
            """
            Logout a peer from the system.
            
            Expected body: {
                "peer_id": "uuid"
            }
            """
            try:
                data = json.loads(body) if body and body != "anonymous" else {}
                response = self.send_to_tracker('logout', data)
                return json.dumps(response)
            except Exception as e:
                return json.dumps({
                    'status': 'error',
                    'message': str(e)
                })
        
        @self.app.route('/health', methods=['GET'])
        def health(headers="guest", body="anonymous"):
            """Health check endpoint."""
            return json.dumps({
                'status': 'success',
                'message': 'Chat WebApp is running',
                'tracker': f'{self.tracker_host}:{self.tracker_port}'
            })
    
    def send_to_tracker(self, method, data):
        """
        Send request to the tracker server.
        
        :param method (str): API method to call.
        :param data (dict): Request data.
        :return (dict): Response from tracker server.
        """
        try:
            # Create socket connection to tracker
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.tracker_host, self.tracker_port))
            
            # Prepare request
            request = {'method': method, **data}
            sock.send(json.dumps(request).encode('utf-8'))
            
            # Receive response
            response_data = sock.recv(4096).decode('utf-8')
            sock.close()
            
            return json.loads(response_data)
        except socket.timeout:
            return {
                'status': 'error',
                'message': 'Tracker server timeout'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to connect to tracker: {str(e)}'
            }
    
    def run(self, ip='0.0.0.0', port=8000):
        """
        Start the web application.
        
        :param ip (str): IP address to bind.
        :param port (int): Port to listen on.
        """
        self.app.prepare_address(ip, port)
        print(f"[ChatWebApp] Starting on {ip}:{port}")
        print(f"[ChatWebApp] Connected to tracker at {self.tracker_host}:{self.tracker_port}")
        self.app.run()


def create_chatapp(ip, port, tracker_host='127.0.0.1', tracker_port=7000):
    """
    Entry point for creating and running the chat web application.
    
    :param ip (str): IP address to bind the web app.
    :param port (int): Port to listen on.
    :param tracker_host (str): Tracker server IP.
    :param tracker_port (int): Tracker server port.
    """
    chat_app = ChatWebApp(tracker_host, tracker_port)
    chat_app.run(ip, port)