import sys
import serial
import json
import argparse

from pfeifferproto import PfeifferProtocol, SerialProtocolViolation, SerialCommunicationError, SerialSimulationDone, SerialProtocolUnknownRegister
from pfeifferrs485 import PfeifferRS485Serial

def pfeifferSnifferCLI():
    ap = argparse.ArgumentParser(description = 'Simple access to Pfeiffer pumps on an RS485 bus attached to a serial port')
    ap.add_argument('-p', '--port', type=str, required=False, default="/dev/ttyU0", help="Serial port to be used to access the RS485 bus")
    ap.add_argument('-s', '--simfile', type=str, required=False, default=None, help="Simulation file. One can supply a JSON dump that should be injected instead of a real serial port")
    ap.add_argument('-d', '--device', type=str, required=False, default=None, action='append', help="Adds a device registerset to a given address (ADR:DEVTYPE). Can be used multiple times")
    ap.add_argument('-j', '--logjson', type=str, required=False, default=None, help="Specifies a logfile that all captured packets are appended to - in JSON format line per line")
    ap.add_argument('--showsim', action='store_true', help="Show simulated messages")
    ap.add_argument('--noshowquery', action='store_true', help="Disable output of query messages")
    ap.add_argument('--noerror', action='store_true', help="Disable error messages (protocol violation, etc.)")
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

    with PfeifferRS485Serial(serialPort, regsets, simulationfile = args.simfile, rawsimulationdump = args.showsim) as port:
        while True:
            try:
                # nextLine = serialNextLine(port)
                # packet = proto.decodePacketRaw(nextLine)

                # Currently decode everything according to TC110 register map
                # packet = proto.decodePacket(packet, proto.registersTC110)
                nextMsg = port.nextMessage()
                if nextMsg['designation'] and nextMsg['payload']:
                    if nextMsg['action'] == 1:
                        if nextMsg['regunit']:
                            unit = nextMsg['regunit']
                        else:
                            unit = ""
                        print("[DECODED] {}, {}: {} {} {}".format(nextMsg['time'], nextMsg['address'], nextMsg['designation'], nextMsg['payload'], unit))
                    else:
                        if not args.noshowquery:
                            print("[DECODED QUERY] {}, {}: {}".format(nextMsg['time'], nextMsg['address'], nextMsg['designation']))
                else:
                    print("[UNKNOWN] {}".format(nextMsg))
                if args.logjson:
                    with open(args.logjson, "a") as f:
                        f.write(json.dumps(nextMsg))
                        f.write("\n")
            except serial.SerialException as e:
                print("Failed to connect to serial port {}".format(portFile))
            except SerialProtocolViolation as e:
                if not args.noerror:
                    print(e)
            except SerialCommunicationError as e:
                if not args.noerror:
                    print(e)
            except SerialProtocolUnknownRegister as e:
                pass
            except KeyboardInterrupt:
                print("\r", end="")
                print("Exiting ...")
                break
            except SerialSimulationDone:
                print("Exiting (simulation done)")
                break

if __name__ == "__main__":
    pfeifferSnifferCLI()
