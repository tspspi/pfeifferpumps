import serial

from pfeifferproto import PfeifferProtocol

class PfeifferRS485Serial:
    def __init__(self, portFile = '/dev/ttyU0'):
        self.proto = PfeifferProtocol()

        self.port = False
        self.port = serial.Serial(portFile, baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=None)

    def __enter__(self, portFile = '/dev/ttyU0'):
        self.proto = PfeifferProtocol()

        self.port = False
        self.port = serial.Serial(portFile, baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=None)

    def __exit__(self, exc_type, exc_value, traceback):
        if self.port:
            self.port.close()
            self.port = False

    def close(self):
        if self.port:
            self.port.close()
            self.port = False
