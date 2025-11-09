"""
daemon.chatserver
~~~~~~~~~~~~~~~~~
This module implements a centralized tracker server for P2P chat application.
It manages peer registration, channel management, and peer discovery.

Requirements:
--------------
- socket: provides socket networking interface.
- threading: enables concurrent client handling via threads.
- json: for message serialization.
"""

import socket
import threading
import json
from datetime import datetime


class ChatServer:
    """
    Centralized tracker server for managing P2P chat peers.
    
    The ChatServer maintains:
    - Active peer list with their IP and port
    - Channel memberships
    - Peer discovery functionality
    
    Attributes:
        host (str): IP address to bind the server.
        port (int): Port number to listen on.
        peers (dict): Dictionary of active peers {peer_id: {ip, port, timestamp}}.
        channels (dict): Dictionary of channels {channel_name: [peer_ids]}.
        lock (threading.Lock): Thread-safe lock for shared data.
    """
    
    def __init__(self, host='0.0.0.0', port=7000):
        """
        Initialize the ChatServer.
        
        :param host (str): IP address to bind.
        :param port (int): Port number to listen on.
        """
        self.host = host
        self.port = port
        self.peers = {}
        self.channels = {}
        self.lock = threading.Lock()
        print(f"[ChatServer] Initialized on {host}:{port}")
    
    def handle_client(self, conn, addr):
        """
        Handle incoming client request.
        
        :param conn (socket.socket): Client connection socket.
        :param addr (tuple): Client address (IP, port).
        """
        try:
            # Receive request
            data = conn.recv(4096).decode('utf-8')
            if not data:
                return
            
            request = json.loads(data)
            method = request.get('method')
            
            print(f"[ChatServer] Received {method} from {addr}")
            
            # Route to appropriate handler
            if method == 'register':
                response = self.register_peer(request)
            elif method == 'get_peers':
                response = self.get_peer_list(request)
            elif method == 'join_channel':
                response = self.join_channel(request)
            elif method == 'leave_channel':
                response = self.leave_channel(request)
            elif method == 'get_channels':
                response = self.get_channels(request)
            elif method == 'logout':
                response = self.logout_peer(request)
            else:
                response = {
                    'status': 'error',
                    'message': f'Unknown method: {method}'
                }
            
            # Send response
            conn.send(json.dumps(response).encode('utf-8'))
            
        except json.JSONDecodeError as e:
            error_response = {'status': 'error', 'message': 'Invalid JSON'}
            conn.send(json.dumps(error_response).encode('utf-8'))
        except Exception as e:
            print(f"[ChatServer] Error handling client: {e}")
            error_response = {'status': 'error', 'message': str(e)}
            conn.send(json.dumps(error_response).encode('utf-8'))
        finally:
            conn.close()
    
    def register_peer(self, request):
        """
        Register a new peer with the tracker.
        
        :param request (dict): Request containing peer_id, ip, port, username.
        :return (dict): Response with status and peer information.
        """
        peer_id = request.get('peer_id')
        peer_ip = request.get('ip')
        peer_port = request.get('port')
        username = request.get('username', 'Anonymous')
        
        if not all([peer_id, peer_ip, peer_port]):
            return {
                'status': 'error',
                'message': 'Missing required fields: peer_id, ip, port'
            }
        
        with self.lock:
            self.peers[peer_id] = {
                'ip': peer_ip,
                'port': peer_port,
                'username': username,
                'timestamp': datetime.now().isoformat()
            }
        
        print(f"[ChatServer] Peer registered: {peer_id} ({username}) at {peer_ip}:{peer_port}")
        
        return {
            'status': 'success',
            'message': 'Peer registered successfully',
            'peer_id': peer_id,
            'username': username
        }
    
    def get_peer_list(self, request):
        """
        Get list of active peers, optionally filtered by channel.
        
        :param request (dict): Request optionally containing channel name.
        :return (dict): Response with peer list.
        """
        channel = request.get('channel', None)
        
        with self.lock:
            if channel and channel in self.channels:
                # Return only peers in specific channel
                peer_ids = self.channels[channel]
                peer_list = {
                    pid: self.peers[pid] 
                    for pid in peer_ids 
                    if pid in self.peers
                }
            else:
                # Return all active peers
                peer_list = self.peers.copy()
        
        return {
            'status': 'success',
            'peers': peer_list,
            'channel': channel,
            'count': len(peer_list)
        }
    
    def join_channel(self, request):
        """
        Add a peer to a channel.
        
        :param request (dict): Request containing peer_id and channel name.
        :return (dict): Response with status.
        """
        peer_id = request.get('peer_id')
        channel = request.get('channel')
        
        if not all([peer_id, channel]):
            return {
                'status': 'error',
                'message': 'Missing required fields: peer_id, channel'
            }
        
        with self.lock:
            # Create channel if not exists
            if channel not in self.channels:
                self.channels[channel] = []
            
            # Add peer to channel
            if peer_id not in self.channels[channel]:
                self.channels[channel].append(peer_id)
        
        print(f"[ChatServer] Peer {peer_id} joined channel: {channel}")
        
        return {
            'status': 'success',
            'message': f'Joined channel: {channel}',
            'channel': channel
        }
    
    def leave_channel(self, request):
        """
        Remove a peer from a channel.
        
        :param request (dict): Request containing peer_id and channel name.
        :return (dict): Response with status.
        """
        peer_id = request.get('peer_id')
        channel = request.get('channel')
        
        if not all([peer_id, channel]):
            return {
                'status': 'error',
                'message': 'Missing required fields: peer_id, channel'
            }
        
        with self.lock:
            if channel in self.channels and peer_id in self.channels[channel]:
                self.channels[channel].remove(peer_id)
                
                # Remove empty channels
                if not self.channels[channel]:
                    del self.channels[channel]
        
        print(f"[ChatServer] Peer {peer_id} left channel: {channel}")
        
        return {
            'status': 'success',
            'message': f'Left channel: {channel}',
            'channel': channel
        }
    
    def get_channels(self, request):
        """
        Get list of channels a peer has joined.
        
        :param request (dict): Request containing peer_id.
        :return (dict): Response with channel list.
        """
        peer_id = request.get('peer_id')
        
        if not peer_id:
            return {
                'status': 'error',
                'message': 'Missing required field: peer_id'
            }
        
        with self.lock:
            user_channels = [
                ch for ch, peers in self.channels.items() 
                if peer_id in peers
            ]
        
        return {
            'status': 'success',
            'channels': user_channels,
            'count': len(user_channels)
        }
    
    def logout_peer(self, request):
        """
        Remove a peer from the system.
        
        :param request (dict): Request containing peer_id.
        :return (dict): Response with status.
        """
        peer_id = request.get('peer_id')
        
        if not peer_id:
            return {
                'status': 'error',
                'message': 'Missing required field: peer_id'
            }
        
        with self.lock:
            # Remove from peers list
            if peer_id in self.peers:
                del self.peers[peer_id]
            
            # Remove from all channels
            for channel in list(self.channels.keys()):
                if peer_id in self.channels[channel]:
                    self.channels[channel].remove(peer_id)
                
                # Remove empty channels
                if not self.channels[channel]:
                    del self.channels[channel]
        
        print(f"[ChatServer] Peer logged out: {peer_id}")
        
        return {
            'status': 'success',
            'message': 'Logged out successfully'
        }
    
    def start(self):
        """
        Start the tracker server and listen for incoming connections.
        """
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(10)
        
        print(f"[ChatServer] Listening on {self.host}:{self.port}")
        
        try:
            while True:
                conn, addr = server_socket.accept()
                thread = threading.Thread(
                    target=self.handle_client, 
                    args=(conn, addr)
                )
                thread.daemon = True
                thread.start()
        except KeyboardInterrupt:
            print("\n[ChatServer] Shutting down...")
        finally:
            server_socket.close()


def create_chatserver(ip, port):
    """
    Entry point for creating and running the chat tracker server.
    
    :param ip (str): IP address to bind the server.
    :param port (int): Port number to listen on.
    """
    server = ChatServer(ip, port)
    server.start()