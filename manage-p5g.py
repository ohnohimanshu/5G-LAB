import os
import fcntl
import socket
import struct
from django.core.management import execute_from_command_line

INTERFACE = "deibr0"   # your interface name

def get_interface_ip(ifname):
    """Return the IPv4 address assigned to a specific interface."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(
            fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR - get interface address
                struct.pack('256s', bytes(ifname[:15], 'utf-8'))
            )[20:24]
        )
    except OSError:
        return None

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_login.settings")

    ip = get_interface_ip(INTERFACE)

    if not ip:
        print(f"❌ Could not find IP for interface: {INTERFACE}")
        exit(1)

    print(f"🚀 Starting Django on interface {INTERFACE} → {ip}:8000")

    execute_from_command_line(["manage.py", "runserver", f"{ip}:8000"])
