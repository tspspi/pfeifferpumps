import sys
import serial

from pfeifferproto import PfeifferProtocol
from pfeifferrs485 import PfeifferRS485Serial

def pfeifferSnifferCLI():
    if len(sys.argv) < 1:
        printUsage()
        return 1

    portFile = '/dev/ttyU0'

    if len(sys.argv) > 1:
        portFile = sys.argv[1]

    try:
        with PfeifferRS485Serial(portFile) as port:
            nextLine = serialNextLine(port)
            packet = proto.decodePacketRaw(nextLine)

            # Currently decode everything according to TC110 register map

            packet = proto.decodePacket(packet, proto.registersTC110)

    except serial.SerialException as e:
        print("Failed to connect to serial port {}".format(portFile))
    except KeyboardInterrupt:
        print("\r", end="")
        print("Exiting ...")

if __name__ == "__main__":
    pfeifferSnifferCLI()
