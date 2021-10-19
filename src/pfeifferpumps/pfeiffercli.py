import sys
import serial
import json
import argparse

from pfeifferproto import PfeifferProtocol, SerialProtocolViolation, SerialCommunicationError, SerialSimulationDone
from pfeifferrs485 import PfeifferRS485Serial

def pfeifferSnifferCLI():
    ap = argparse.ArgumentParser(description = 'Simple access to Pfeiffer pumps on an RS485 bus attached to a serial port')
    ap.add_argument('-p', '--port', type=str, required=False, default="/dev/ttyU0", help="Serial port to be used to access the RS485 bus")
    ap.add_argument('-s', '--simfile', type=str, required=False, default=None, help="Simulation file. One can supply a JSON dump that should be injected instead of a real serial port")
    ap.add_argument('-d', '--device', type=str, required=False, default=None, action='append', help="Adds a device registerset to a given address (ADR:DEVTYPE). Can be used multiple times")
    ap.add_argument('-j', '--logjson', type=str, required=False, default=None, help="Specifies a logfile that all captured packets are appended to - in JSON format line per line")
    args = ap.parse_args()

    serialPort = args.port
    regsets = { }
    for devspec in args.device:
        devspecparts = devspec.split(':')
        if len(devspecparts) != 2:
            print("Invalid device address : name specification {}".format(devspec[0]))
            exit(1)
        try:
            adr = int(devspecparts[0])
        except ValueError:
            print("Invalid device address {}".format(devspec[0]))
            exit(1)
        regsets[adr] = devspecparts[1]

    with PfeifferRS485Serial(serialPort, regsets, simulationfile = args.simfile) as port:
        while True:
            try:
                # nextLine = serialNextLine(port)
                # packet = proto.decodePacketRaw(nextLine)

                # Currently decode everything according to TC110 register map
                # packet = proto.decodePacket(packet, proto.registersTC110)
                nextMsg = port.nextMessage()
                print(nextMsg)
                if args.logjson:
                    with open(args.logjson, "a") as f:
                        f.write(json.dumps(nextMsg))
                        f.write("\n")
            except serial.SerialException as e:
                print("Failed to connect to serial port {}".format(portFile))
            except SerialProtocolViolation as e:
                print(e)
            except SerialCommunicationError as e:
                print(e)
            except KeyboardInterrupt:
                print("\r", end="")
                print("Exiting ...")
                break
            except SerialSimulationDone:
                print("Exiting (simulation done)")
                break

if __name__ == "__main__":
    pfeifferSnifferCLI()
