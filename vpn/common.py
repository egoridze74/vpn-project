import os
import struct
import fcntl
import threading
import select


TUNSETIFF = 0x400454ca
IFF_TUN = 0x0001
IFF_NO_PI = 0x1000

def xor_encrypt(data, key=0x5A):
    return bytes(b ^ key for b in data)

def create_tun(name):
    if not os.path.exists("/dev/net/tun"):
        os.makedirs("/dev/net", exist_ok=True)
        try:
            os.mknod("/dev/net/tun", mode=0o666, device=os.makedev(10, 200))
        except:
            pass
    
    tun = os.open("/dev/net/tun", os.O_RDWR)
    ifr = struct.pack('16sH', name.encode(), IFF_TUN | IFF_NO_PI)
    fcntl.ioctl(tun, TUNSETIFF, ifr)
    
    import subprocess
    subprocess.run(["ip", "link", "set", name, "up"], capture_output=True)
    
    return tun

def start_tunnel(tun_fd, udp_sock, remote_addr):
    running = True
    
    def tun_to_udp():
        while running:
            try:
                ready, _, _ = select.select([tun_fd], [], [], 0.1)
                if ready:
                    packet = os.read(tun_fd, 4096)
                    if packet:
                        udp_sock.sendto(xor_encrypt(packet), remote_addr)
            except OSError:
                break
            except Exception as e:
                print(f"TUN->UDP error: {e}")
                break
    
    def udp_to_tun():
        while running:
            try:
                ready, _, _ = select.select([udp_sock], [], [], 0.1)
                if ready:
                    data, _ = udp_sock.recvfrom(8192)
                    os.write(tun_fd, xor_encrypt(data))
            except OSError:
                break
            except Exception as e:
                print(f"UDP->TUN error: {e}")
                break
    
    t1 = threading.Thread(target=tun_to_udp, daemon=True)
    t2 = threading.Thread(target=udp_to_tun, daemon=True)
    t1.start()
    t2.start()
    return t1, t2
