import socket
import time

class DirectATE:
    """Direct UDP driver for ATE, bypassing EPICS."""
    def __init__(self, ip_address='10.69.26.3', port=5000):
        self.ip = ip_address
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(3)
        self.server_address = (self.ip, self.port)

    def send_cmd(self, msg: bytes):
        try:
            self.sock.sendto(msg + b'\n', self.server_address)
            time.sleep(0.1)
        except Exception as e:
            print(f"ATE UDP Error: {e}")

    def set_mode(self, chan: int, mode: str):
        val = '1' if mode == 'CAL' else '0'
        self.send_cmd(f"T{chan}{val}".encode('UTF-8'))

    def set_cal_dac(self, val: float):
        # Matches old script logic (val * 50)
        cmd = f"CALDAC{val*50.0}".encode('UTF-8')
        # Send multiple times to ensure UDP receipt (paranoid like old script)
        for _ in range(3):
            self.send_cmd(cmd)

    def set_cal_dac_w_os(self, current: float):
        # Wrapper to match expected method signature if needed
        self.set_cal_dac(current)

    def init_channels(self):
        for x in ['1', '2', '3', '4']:
            self.send_cmd(f"T{x}0".encode('UTF-8'))
        self.send_cmd(b"CAL0")