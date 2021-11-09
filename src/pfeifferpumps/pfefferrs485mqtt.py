import serial
import json
import argparse
import sys
import logging
import time

import signal, lockfile, grp, os
from pwd import getpwnam
from daemonize import Daemonize

import paho.mqtt.client as mqtt

from pfeifferproto import PfeifferProtocol, SerialProtocolViolation, SerialSimulationDone
from pfeifferrs485 import PfeifferRS485Serial
from datetime import datetime

# Simple daemon to provide a bridge between the RS485 bus that Pfeiffer pumps
# are using and MQTT (or possibly other backends such as logging systems)
# The daemon basically:
#   - Can be triggered to re read the configuration file. In this case it
#     drops any open serial port (!) and any network connection. This of course
#     means one could miss messages
#   - In case of a lost serial port stays in a loop that re-reads the configuration
#     and tries to open re-open the serial port. It does not terminate (!)
#   - In case of a lost MQTT connection runs as usual but does not cache any
#     messages.
#
# To trigger these actions from the outside global variables CAN be used (which
# is done from inside the signal handlers)

class pfeifferRS485MqttBridgeDaemon:
    def __init__(self, args, logger, debugMode = False):
        self.debugMode = debugMode
        self.args = args
        self.logger = logger
        self.terminate = False
        self.rereadConfig = True
        self.mqtt = None

    def signalSigHup(self, *args):
        self.rereadConfig = True

    def signalTerm(self, *args):
        self.terminate = True

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        pass

    def run(self):
        if self.debugMode:
            self.logger.debug("Running in foreground mode")
        else:
            self.logger.debug("Running in daemon mode")

        # Set signal handlers for:

        signal.signal(signal.SIGHUP, self.signalSigHup)
        signal.signal(signal.SIGTERM, self.signalTerm)
        signal.signal(signal.SIGINT, self.signalTerm)

        while True:
            # First read all configuration. In this state there is no open
            # serial port and no open network connection

            # Now open the MQTT connection. Loop until this works and our serial
            # port stays open

            # Handle messages in both ways - received messages from RS485 get
            # published to MQTT and the other way round ...
            if self.terminate:
                break

            try:
                with open(self.args.config) as cfgfile:
                    configData = json.load(cfgfile)
            except Exception as e:
                self.logger.error("Failed to read JSON configuration file{}".format(self.args.config))
                self.logger.error(e)
                time.sleep(5)
                continue

            self.logger.debug("Loaded configuration data")

            # Open any configured serial ports ...
            serialSuccess = True
            serialPorts = []
            for portspec in configData['ports']:
                regsets = {}
                self.logger.debug("Configuring port {} with {} devices".format(portspec['port'], len(portspec['devices'])))
                for strAdress in portspec['devices']:
                    try:
                        adr = int(strAdress)
                    except ValueError:
                        self.logger.error("Invalid device address {}".format(strAdress))
                        serialSuccess = False
                        break
                    regsets[adr] = portspec['devices'][strAdress]
                if not serialSuccess:
                    break

                try:
                    if "simfile" in portspec:
                        newPort = PfeifferRS485Serial(portspec['port'], regsets, simulationfile = portspec['simfile'], pollingAsync = True)
                    else:
                        newPort = PfeifferRS485Serial(portspec['port'], regsets, pollingAsync = True)
                    serialPorts.append(newPort)
                except Exception as e:
                    self.logger.error("Failed to initialize port {}".format(portspec['port']))
                    self.logger.error(e)
                    serialSuccess = False

            if not serialSuccess:
                self.logger.error("Failed to configure ports, retrying")
                time.sleep(5)
                for port in serialPorts:
                    port.close()
                continue

            self.logger.debug("Initialized and configured serial ports")

            # MQTT initialization. Since we can only connect to a single broker

            if not "mqtt" in configData:
                self.logger.error("Missing MQTT configuration")
                time.sleep(5)
                for port in serialPorts:
                    port.close()
                continue
            if not "host" in configData['mqtt']:
                self.logger.error("Missing MQTT host parameter")
                time.sleep(5)
                for port in serialPorts:
                    port.close()
                continue
            if not "port" in configData['mqtt']:
                self.logger.error("Missing MQTT port parameter")
                time.sleep(5)
                for port in serialPorts:
                    port.close()
                continue
            if not "user" in configData['mqtt']:
                self.logger.error("Missing MQTT user name")
                time.sleep(5)
                for port in serialPorts:
                    port.close()
                continue
            if not "password" in configData['mqtt']:
                self.logger.error("Missing MQTT password")
                time.sleep(5)
                for port in serialPorts:
                    port.close()
                continue
            if not "clientid" in configData['mqtt']:
                self.logger.error("Missing MQTT client id")
                time.sleep(5)
                for port in serialPorts:
                    port.close()
                continue

            try:
                self.mqtt = mqtt.Client(client_id=configData['mqtt']['clientid'], clean_session=True)
                self.mqtt.username_pw_set(username=configData['mqtt']['user'], password=configData['mqtt']['password'])
                self.mqtt.connect(
                    configData['mqtt']['host'],
                    port = configData['mqtt']['port']
                )
            except Exception as e:
                self.logger.error("Failed to connect with MQTT server")
                self.logger.error(e)
                for port in serialPorts:
                    port.close()
                time.sleep(5)




            # Cleanup: Close serial ports ...
            for port in serialPorts:
                port.close()

            time.sleep(5)

        self.logger.info("Shutting down due to user request")


# The following functions are only used for startup handling
# The daemon can either start in foreground or in a daemonized version - this
# is handled by:
#
#   pfeifferrs485mqttBridge()   is the main startup function that determines if
#                               and in case how the service should daemonize
#   mainDaemon()                is a trampoline function that is launched by
#                               daemonize
#   parseArguments()            Is an utility function that parses arguments and
#                               configures the logger since this has to be done
#                               again in case the daemoniation process is run due
#                               to argument passing limitations
#
# In any case the daemon ends up in the pfeifferRS485MqttBridgeDaemon.run() method
# with a working logger

def mainDaemon():
    parg = parseArguments()
    args = parg['args']
    logger = parg['logger']

    logger.debug("Running in background")
    with pfeifferRS485MqttBridgeDaemon(args, logger, debugMode = False) as bridge:
        bridge.run()

def parseArguments():
    ap = argparse.ArgumentParser(description = 'MQTT bridge for Pfeiffer pumps on an RS485 bus attached to a serial port')
    ap.add_argument('-p', '--port', type=str, required=False, default="/dev/ttyU0", help="Serial port to be used to access the RS485 bus")
    ap.add_argument('-s', '--simfile', type=str, required=False, default=None, help="Simulation file. One can supply a JSON dump that should be injected instead of a real serial port")
    ap.add_argument('-f', '--foreground', action='store_true', help="Do not daemonize - stay in foreground and dump debug information to the terminal")

    ap.add_argument('-m', '--mode', type=str, required=False, default="ro", help="Mode selection: Read only (ro, default) or read/write mode (rw)")
    ap.add_argument('-c', '--config', type=str, required=False, default="/etc/pfeiffermqtt.conf", help="JSON configuration file for MQTT bridge")

    ap.add_argument('--uid', type=str, required=False, default=None, help="User ID to impersonate when launching as root")
    ap.add_argument('--gid', type=str, required=False, default=None, help="Group ID to impersonate when launching as root")
    ap.add_argument('--chroot', type=str, required=False, default=None, help="Chroot directory that should be switched into")
    ap.add_argument('--pidfile', type=str, required=False, default="/var/run/pfeiffermqtt.pid", help="PID file to keep only one daemon instance running")
    ap.add_argument('--loglevel', type=str, required=False, default="error", help="Loglevel to use (debug, info, warning, error, critical). Default: error")
    ap.add_argument('--logfile', type=str, required=False, default=None, help="Logfile that should be used as target for log messages")

    args = ap.parse_args()
    loglvls = {
        "DEBUG"     : logging.DEBUG,
        "INFO"      : logging.INFO,
        "WARNING"   : logging.WARNING,
        "ERROR"     : logging.ERROR,
        "CRITICAL"  : logging.CRITICAL
    }
    if not args.loglevel.upper() in loglvls:
        print("Unknown log level {}".format(args.loglevel.upper()))
        sys.exit(1)

    logger = logging.getLogger()
    logger.setLevel(loglvls[args.loglevel.upper()])
    if args.logfile:
        fileHandleLog = logging.FileHandler(args.logfile)
        logger.addHandler(fileHandleLog)

    return { 'args' : args, 'logger' : logger }

# Entry function for CLI program
# This also configures the daemon properties

def pfeifferrs485mqttBridge():
    parg = parseArguments()
    args = parg['args']
    logger = parg['logger']

    daemonPidfile = args.pidfile
    daemonUid = None
    daemonGid = None
    daemonChroot = "/"

    if args.uid:
        try:
            args.uid = int(args.uid)
        except ValueError:
            try:
                args.uid = getpwnam(args.uid).pw_uid
            except KeyError:
                logger.critical("Unknown user {}".format(args.uid))
                print("Unknown user {}".format(args.uid))
                sys.exit(1)
        daemonUid = args.uid
    if args.gid:
        try:
            args.gid = int(args.gid)
        except ValueError:
            try:
                args.gid = grp.getgrnam(args.gid)[2]
            except KeyError:
                logger.critical("Unknown group {}".format(args.gid))
                print("Unknown group {}".format(args.gid))
                sys.exit(1)

        daemonGid = args.gid

    if args.chroot:
        if not os.path.isdir(args.chroot):
            logger.critical("Non existing chroot directors {}".format(args.chroot))
            print("Non existing chroot directors {}".format(args.chroot))
            sys.exit(1)
        daemonChroot = args.chroot

    if args.foreground:
        logger.debug("Launching in foreground")
        with pfeifferRS485MqttBridgeDaemon(args, logger, debugMode = True) as bridge:
            bridge.run()
    else:
        logger.debug("Daemonizing ...")
        daemon = Daemonize(
            app="PfeifferRS485MQTTBridge",
            action=mainDaemon,
            pid=daemonPidfile,
            user=daemonUid,
            group=daemonGid,
            chdir=daemonChroot
        )
        daemon.start()


if __name__ == "__main__":
    pfeifferrs485mqttBridge()
