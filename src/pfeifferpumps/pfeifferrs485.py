import serial


from pfeifferproto import PfeifferProtocol, SerialProtocolViolation

class PfeifferRS485Serial:
    def __init__(self, portFile = '/dev/ttyU0', registersets = None):
        self.proto = PfeifferProtocol()
        self.registerset = registersets
        if registersets:
            if not isinstance(registersets, dict):
                raise SerialProtocolViolation('Register sets has to be a dictionary from address to register set identifier')
            for address, regset in registersets.items():
                if not regset in self.proto.registers:
                    raise SerialProtocolViolation("Unknown register set {} for address {}".format(regset, address))

        self.port = False
        self.port = serial.Serial(portFile, baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=None)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.port:
            self.port.close()
            self.port = False

    def close(self):
        if self.port:
            self.port.close()
            self.port = False

    def nextMessage(self):
        if not self.port:
            raise SerialCommunicationError('Serial port not connected')

        line = self.serialReadNextLine()
        packetRaw = self.proto.decodePacketRaw(line)
        if self.registerset:
            # Check if we have a protocol decoder / registerset for the given
            # address and if apply the decode routine
            if packetRaw["address"] in self.registerset:
                regset = self.registerset[packetRaw["address"]]
                packetRaw = self.proto.decodePacket(packetRaw, self.proto.registers[regset])

        return packetRaw

    # Some internal utility functions
    # Do not use from the outside!

    def serialReadNextLine(self):
        if not self.port:
            raise SerialCommunicationError("Port not ready")

        line = bytearray()
        eol = b'\r'
        while True:
            c = self.port.read(1)
            if c:
                if ((c < 0x20) or (c > 0x7F)) and (c != 0x0D):
                    raise SerialProtocolViolation('Protocol violation. Encountered illegal byte')
                line = line + c
                if line[:-1] == eol:
                    break
            else:
                raise SerialCommunicationError('Serial communication error')

        return line.decode()
