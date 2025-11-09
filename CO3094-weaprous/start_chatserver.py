"""
start_chatserver
~~~~~~~~~~~~~~~~~
Entry point for launching the chat tracker server.

This script starts the centralized tracker server that manages
peer registration, channel membership, and peer discovery for
the P2P chat application.

Usage:
    python start_chatserver.py --server-ip 0.0.0.0 --server-port 7000
"""

import argparse
from daemon.chatserver import create_chatserver

# Default port for chat tracker server
CHAT_SERVER_PORT = 7000

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='ChatServer',
        description='Chat Tracker Server for P2P Chat Application',
        epilog='Manages peer registration and channel membership'
    )
    
    parser.add_argument(
        '--server-ip',
        default='0.0.0.0',
        help='IP address to bind the server (default: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--server-port',
        type=int,
        default=CHAT_SERVER_PORT,
        help=f'Port number to listen on (default: {CHAT_SERVER_PORT})'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Chat Tracker Server")
    print("=" * 60)
    print(f"Server IP:   {args.server_ip}")
    print(f"Server Port: {args.server_port}")
    print("=" * 60)
    
    # Start the chat tracker server
    create_chatserver(args.server_ip, args.server_port)