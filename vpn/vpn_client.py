import os
import socket
import json
import threading

from common import xor_encrypt, create_tun, start_tunnel


class VPNClient:
    def __init__(self, server_ip="127.0.0.1", server_port=1194):
        self.server_ip = server_ip
        self.server_port = server_port
        self.udp_sock = None
        self.tun_fd = None
        self.authenticated = False
        
    def authenticate(self, username, password):
        print(f"Authenticating as '{username}'...")
        
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.settimeout(5)
        
        request = {'username': username, 'password': password}
        encrypted = xor_encrypt(json.dumps(request).encode())
        self.udp_sock.sendto(encrypted, (self.server_ip, self.server_port))
        
        try:
            data, _ = self.udp_sock.recvfrom(4096)
            response = json.loads(xor_encrypt(data).decode())
            
            if response.get('status') == 'authenticated':
                self.authenticated = True
                print("Authentication successful")
                return True
            else:
                print(f"Auth failed: {response.get('message')}")
                return False
        except Exception as e:
            print(f"Auth error: {e}")
            return False
    
    def start(self, username, password):
        if not self.authenticate(username, password):
            return
        
        self.tun_fd = create_tun("tun_client")
        if not self.tun_fd:
            print("Failed to create TUN")
            return
        
        import subprocess
        subprocess.run(["ip", "addr", "add", "10.0.0.2/24", "dev", "tun_client"], capture_output=True)
        
        print("VPN Connected")
        print("You can now use: ping 10.0.0.1")
        
        start_tunnel(self.tun_fd, self.udp_sock, (self.server_ip, self.server_port))
        
        try:
            while True:
                threading.Event().wait(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        if self.tun_fd:
            os.close(self.tun_fd)
        if self.udp_sock:
            self.udp_sock.close()
        print("VPN disconnected")


if __name__ == "__main__":
    client = VPNClient(server_ip="127.0.0.1", server_port=1194)
    username = input("Username: ")
    password = input("Password: ")
    client.start(username, password)