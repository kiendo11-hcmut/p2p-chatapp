"""
start_chatapp
~~~~~~~~~~~~~~~~~
Entry point for launching the chat web application.

This script starts the RESTful web application that provides
HTTP APIs for the chat system, connecting to the tracker server.

Usage:
    python start_chatapp.py --server-ip 0.0.0.0 --server-port 8000 \
                            --tracker-ip 127.0.0.1 --tracker-port 7000
"""

import argparse
from apps.chatapp import create_chatapp

# Default ports
WEBAPP_PORT = 8000
TRACKER_PORT = 7000

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='ChatWebApp',
        description='Chat Web Application with RESTful APIs',
        epilog='Provides HTTP interface to the chat tracker server'
    )
    
    parser.add_argument(
        '--server-ip',
        default='0.0.0.0',
        help='IP address to bind the web app (default: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--server-port',
        type=int,
        default=WEBAPP_PORT,
        help=f'Port number for web app (default: {WEBAPP_PORT})'
    )
    
    parser.add_argument(
        '--tracker-ip',
        default='127.0.0.1',
        help='IP address of the tracker server (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--tracker-port',
        type=int,
        default=TRACKER_PORT,
        help=f'Port of the tracker server (default: {TRACKER_PORT})'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Chat Web Application")
    print("=" * 60)
    print(f"WebApp IP:      {args.server_ip}")
    print(f"WebApp Port:    {args.server_port}")
    print(f"Tracker IP:     {args.tracker_ip}")
    print(f"Tracker Port:   {args.tracker_port}")
    print("=" * 60)
    
    # Start the chat web application
    create_chatapp(
        args.server_ip,
        args.server_port,
        args.tracker_ip,
        args.tracker_port
    )