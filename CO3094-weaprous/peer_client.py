"""
peer_client
~~~~~~~~~~~~~~~~~
P2P Chat Client implementation.

Usage:
    python peer_client.py
"""

import socket
import threading
import json
import uuid
import sys
from colorama import init, Fore, Style

init(autoreset=True)
class PeerClient:
    def __init__(self, tracker_host, tracker_port, listen_port, username='Anonymous'):
        self.tracker_host = tracker_host
        self.tracker_port = tracker_port
        self.listen_port = listen_port
        self.username = username
        self.peer_id = str(uuid.uuid4())[:8]
        self.connections = {}  # {peer_id: {'socket': sock, 'username': username}}
        self.channels = []
        self.running = True
        self.current_channel = None
        print(Fore.CYAN + f"[Peer] Initialized as {username} (ID: {self.peer_id})")
    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return '127.0.0.1'

    def send_to_tracker(self, method, data):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.tracker_host, self.tracker_port))
            request = {'method': method, **data}
            sock.send(json.dumps(request).encode('utf-8'))
            response = sock.recv(4096).decode('utf-8')
            sock.close()
            return json.loads(response)
        except Exception as e:
            print(Fore.RED + f"[Peer] Error contacting tracker: {e}")
            return {'status': 'error', 'message': str(e)}

    def register(self):
        data = {
            'peer_id': self.peer_id,
            'ip': self.get_local_ip(),
            'port': self.listen_port,
            'username': self.username
        }
        response = self.send_to_tracker('register', data)
        if response.get('status') == 'success':
            print(Fore.GREEN + "[Peer] Registered with tracker successfully")
        else:
            print(Fore.RED + f"[Peer] Registration failed: {response.get('message')}")
        return response

    def join_channel(self, channel_name):
        data = {'peer_id': self.peer_id, 'channel': channel_name}
        response = self.send_to_tracker('join_channel', data)
        if response.get('status') == 'success':
            if channel_name not in self.channels:
                self.channels.append(channel_name)
            self.current_channel = channel_name
            print(Fore.GREEN + f"[Peer] Joined channel: {channel_name}")
            self.connect_to_channel_peers(channel_name)
        else:
            print(Fore.RED + f"[Peer] Failed to join channel: {response.get('message')}")
        return response

    def connect_to_channel_peers(self, channel):
        data = {'peer_id': self.peer_id, 'channel': channel}
        response = self.send_to_tracker('get_peers', data)
        if response.get('status') == 'success':
            peers = response.get('peers', {})
            for peer_id, peer_info in peers.items():
                if peer_id != self.peer_id and peer_id not in self.connections:
                    self.connect_to_peer(peer_id, peer_info['ip'], peer_info['port'], peer_info.get('username', 'Unknown'))

    def connect_to_peer(self, peer_id, ip, port, username='Unknown'):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, port))
            handshake = {'type': 'handshake', 'peer_id': self.peer_id, 'username': self.username}
            sock.send(json.dumps(handshake).encode('utf-8'))
            self.connections[peer_id] = {'socket': sock, 'username': username}
            thread = threading.Thread(target=self.listen_to_peer, args=(peer_id, sock))
            thread.daemon = True
            thread.start()
            print(Fore.MAGENTA + f"[P2P] Connected to {username} ({peer_id})")
        except Exception as e:
            print(Fore.RED + f"[P2P] Failed to connect to {peer_id}: {e}")

    def listen_to_peer(self, peer_id, sock):
        try:
            while self.running:
                data = sock.recv(4096).decode('utf-8')
                if not data:
                    break
                try:
                    message = json.loads(data)
                    self.handle_incoming_message(peer_id, message)
                except json.JSONDecodeError:
                    continue
        except:
            pass
        finally:
            if peer_id in self.connections:
                del self.connections[peer_id]
            sock.close()

    def handle_incoming_message(self, peer_id, message):
        if message.get('type') == 'chat':
            channel = message.get('channel', 'unknown')
            sender = message.get('username', peer_id)
            content = message.get('content', '')
            # Hiển thị tin nhắn peer chuẩn format
            print(Fore.YELLOW + f"\n[{sender} @{channel}]> {content}")
            # Hiển thị lại prompt nhập tin nhắn cho user
            if self.current_channel == channel:
                print(Fore.CYAN + f"{self.username} @{self.current_channel}> ", end='', flush=True)

    def send_message(self, channel, content):
        message = {'type':'chat', 'channel': channel, 'peer_id': self.peer_id, 'username': self.username, 'content': content}
        message_json = json.dumps(message).encode('utf-8')
        for peer_id, pdata in list(self.connections.items()):
            try:
                pdata['socket'].send(message_json)
            except:
                del self.connections[peer_id]

    def start_listening(self):
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('0.0.0.0', self.listen_port))
            server_socket.listen(5)
            while self.running:
                try:
                    conn, addr = server_socket.accept()
                    thread = threading.Thread(target=self.handle_incoming_connection, args=(conn,))
                    thread.daemon = True
                    thread.start()
                except:
                    continue
        except Exception as e:
            print(Fore.RED + f"[P2P] Listener error: {e}")

    def handle_incoming_connection(self, conn):
        try:
            data = conn.recv(4096).decode('utf-8')
            handshake = json.loads(data)
            if handshake.get('type') == 'handshake':
                peer_id = handshake.get('peer_id')
                username = handshake.get('username', 'Unknown')
                self.connections[peer_id] = {'socket': conn, 'username': username}
                thread = threading.Thread(target=self.listen_to_peer, args=(peer_id, conn))
                thread.daemon = True
                thread.start()
        except:
            conn.close()

    def logout(self):
        data = {'peer_id': self.peer_id}
        try:
            self.send_to_tracker('logout', data)
        except:
            pass

    def stop(self):
        self.running = False
        self.logout()
        for pdata in self.connections.values():
            try:
                pdata['socket'].close()
            except:
                pass

def main():
    print("="*60)
    print("P2P Chat Client")
    print("="*60)
    username = input("Enter your username: ").strip() or 'Anonymous'
    tracker_host = input("Tracker IP (default: 127.0.0.1): ").strip() or '127.0.0.1'
    tracker_port = int(input("Tracker port (default: 7000): ").strip() or '7000')
    listen_port = int(input("Your listen port (default: 9001): ").strip() or '9001')

    peer = PeerClient(tracker_host, tracker_port, listen_port, username)
    peer.register()

    listener_thread = threading.Thread(target=peer.start_listening)
    listener_thread.daemon = True
    listener_thread.start()

    print("\nCommands:")
    print("  /join <channel>     - Join a channel")
    print("  /channels           - List your channels")
    print("  /peers              - Show connected peers")
    print("  /quit               - Exit\n")

    try:
        while True:
            if peer.current_channel:
                cmd = input(f"{peer.username} @{peer.current_channel}> ").strip()
            else:
                cmd = input("> ").strip()
            if not cmd:
                continue
            if cmd.startswith('/join '):
                channel = cmd.split(' ',1)[1]
                peer.join_channel(channel)
            elif cmd == '/channels':
                print(f"Your channels: {', '.join(peer.channels) if peer.channels else 'None'}")
            elif cmd == '/peers':
                print(f"Connected peers ({len(peer.connections)}):")
                for pid, pdata in peer.connections.items():
                    print(f"  - {pdata['username']} ({pid})")
            elif cmd == '/quit':
                peer.stop()
                print("Goodbye!")
                break
            elif peer.current_channel:
                peer.send_message(peer.current_channel, cmd)
    except KeyboardInterrupt:
        peer.stop()
        print("\nShutting down...")

if __name__ == '__main__':
    main()
