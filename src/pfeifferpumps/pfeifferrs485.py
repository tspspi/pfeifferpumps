import serial
import json

from pfeifferproto import PfeifferProtocol, SerialProtocolViolation, SerialSimulationDone
from datetime import datetime

class PfeifferRS485Serial:
    def __init__(self, portFile = '/dev/ttyU0', registersets = None, simulationfile = None):
        self.proto = PfeifferProtocol()
        self.registerset = registersets
        if registersets:
            if not isinstance(registersets, dict):
                raise SerialProtocolViolation('Register sets has to be a dictionary from address to register set identifier')
            for address, regset in registersets.items():
                if not regset in self.proto.registers:
                    raise SerialProtocolViolation("Unknown register set {} for address {}".format(regset, address))

        self.port = False
        self.simfile = False
        if simulationfile == None:
            self.port = serial.Serial(portFile, baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=None)
        else:
            self.simfile = open(simulationfile, "r")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.port:
            self.port.close()
            self.port = False
        if self.simfile:
            self.simfile.close()
            self.simple = False

    def close(self):
        if self.port:
            self.port.close()
            self.port = False
        if self.simfile:
            self.simfile.close()
            self.simple = False

    def nextMessage(self):
        if (not self.port) and (not self.simfile):
            raise SerialCommunicationError('Serial port not connected')

        line = self.serialReadNextLine()
        packetRaw = self.proto.decodePacketRaw(line)
        if self.registerset:
            # Check if we have a protocol decoder / registerset for the given
            # address and if apply the decode routine
            if packetRaw["address"] in self.registerset:
                regset = self.registerset[packetRaw["address"]]
                packetRaw = self.proto.decodePacket(packetRaw, self.proto.registers[regset])

        # For all received packages we append a timestamp ...
        tmNow = datetime.now()
        packetRaw["time"] = str(tmNow)
        packetRaw["timestamp"] = int(tmNow.timestamp())

        return packetRaw

    # Some internal utility functions
    # Do not use from the outside!

    def serialReadNextLine(self):
        if (not self.port) and (not self.simfile):
            raise SerialCommunicationError("Port not ready")

        if self.port:
            line = ""
            eol = "\r"
            while True:
                c = self.port.read(1)
                c = ord(c)
                if c:
                    if ((c < 0x20) or (c > 0x7F)) and (c != 0x0D):
                        raise SerialProtocolViolation('Protocol violation. Encountered illegal byte {}'.format(c))
                        pass
                    else:
                        line = line + chr(c)
                        if c == 0x0D:
                            break
                else:
                    raise SerialCommunicationError('Serial communication error')

            return line
        else:
            line = self.simfile.readline()
            if line:
                packet = json.loads(line)
                line = packet['packetRaw']
                print("[SIMULATION] Simulating packet: {}".format(line))
                return line
            else:
                raise SerialSimulationDone('End of simulation')
