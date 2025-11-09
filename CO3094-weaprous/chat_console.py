# chat_console.py
import threading
from peer_client import PeerClient

def main():
    tracker_host = input("Enter tracker server IP (default: 127.0.0.1): ") or '127.0.0.1'
    tracker_port = int(input("Enter tracker port (default: 8000): ") or '8000')
    listen_port = int(input("Enter your listen port (default: 9001): ") or '9001')
    
    # Tạo peer client
    peer = PeerClient(tracker_host, tracker_port, listen_port)
    
    # Đăng ký với tracker
    peer.register()
    
    # Khởi động P2P listener trong thread riêng
    listener_thread = threading.Thread(target=peer.start_listening)
    listener_thread.daemon = True
    listener_thread.start()
    
    print("\nCommands:")
    print("  /join <channel> - Join a channel")
    print("  /channels - List your channels")
    print("  /send <channel> <message> - Send message to channel")
    print("  /quit - Exit")
    
    current_channel = None
    
    while True:
        try:
            cmd = input("\n> ").strip()
            
            if not cmd:
                continue
            
            if cmd.startswith('/join '):
                channel = cmd.split(' ', 1)[1]
                response = peer.join_channel(channel)
                print(f"Joined channel: {channel}")
                current_channel = channel
            
            elif cmd == '/channels':
                print(f"Your channels: {', '.join(peer.channels)}")
            
            elif cmd.startswith('/send '):
                parts = cmd.split(' ', 2)
                if len(parts) < 3:
                    print("Usage: /send <channel> <message>")
                else:
                    channel = parts[1]
                    message = parts[2]
                    peer.send_message(channel, message)
                    print(f"Sent to {channel}: {message}")
            
            elif cmd == '/quit':
                peer.stop()
                break
            
            elif current_channel:
                # Gửi message đến channel hiện tại
                peer.send_message(current_channel, cmd)
                print(f"[{current_channel}] You: {cmd}")
            
            else:
                print("Unknown command or no channel selected")
        
        except KeyboardInterrupt:
            peer.stop()
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    main()