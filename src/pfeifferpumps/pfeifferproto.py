class SerialProtocolViolation(Exception):
    pass

class SerialProtocolUnknownRegister(Exception):
    pass

class SerialCommunicationError(Exception):
    pass

class SerialSimulationDone(Exception):
    pass

class PfeifferProtocol:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        pass
    def __init__(self):
        pass
    def decodePacketRaw(self, line):
        if len(line) < 14:
            raise SerialProtocolViolation('Protocol violation. Sentence too short')
        if line[-1] != '\r':
            raise SerialProtocolViolation('Protocol violation. Sentence not ended with carriage return')

        devAddress = line[:3]
        devAction = line[3]

        # The following check should verify if the byte at position 5 is
        # always 0 as specified in the docs. This does not seem to be a valid
        # constraint in reality?

        # if line[4] != '0':
        #    raise SerialProtocolViolation('Protocol violation. Byte at position 5 is not 0')

        devParamNumber = line[5:8]
        msgDataLength = line[8:10]

        # Now calculate checksum
        chkSum = 0
        realChkSum = sum(bytearray(line[:-4].encode(encoding = "ASCII"))) % 256
        if realChkSum != int(line[-4:-1]):
            raise SerialProtocolViolation('Protocol violation. Checksum invalid')

        # In case the checksum passes return an dictionary containing the required information
        return {
            "address"       : int(devAddress),
            "param"         : int(devParamNumber),
            "action"        : int(devAction),
            "payloadRaw"    : line[10:-4],
            "payloadLength" : int(msgDataLength),
            "packetRaw"     : line
        }

    def decodeDataType_0(self, payload):
        if len(payload) != 6:
            raise SerialProtocolViolation('Datatype boolean_old has to be 6 characters long')
        if payload == '111111':
            return True
        if payload == '000000':
            return False
        raise SerialProtocolViolation('Unknown boolean_old value '+payload)

    def decodeDataType_1(self, payload):
        if len(payload) != 6:
            raise SerialProtocolViolation('Datatype u_integer has to be 6 characters long')
        for i in range(0, len(payload)):
            if (ord(payload[i]) < 0x30) or (ord(payload[i]) > 0x39):
                raise SerialProtocolViolation('Invalid non ASCII number character in u_integer payload '+payload)
        return int(payload)

    def decodeDataType_2(self, payload):
        if len(payload) != 6:
            raise SerialProtocolViolation('Datatype u_real has to be 6 characters long')
        for i in range(0, len(payload)):
            if (ord(payload[i]) < 0x30) or (ord(payload[i]) > 0x39):
                raise SerialProtocolViolation('Invalid non ASCII number character in u_real payload '+payload)
        return float(payload)/100.0

    def decodeDataType_3(self, payload):
        if len(payload) != 6:
            raise SerialProtocolViolation('Datatype u_expo has to be 6 characters long')
        try:
            num = float(payload)
        except Exception:
            raise SerialProtocolViolation('Invalid number '+payload+' for u_expo')
        return num

    def decodeDataType_4(self, payload):
        # NOTE: Strings now seem to have (other than documentation)
        # if len(payload) != 6:
        #    raise SerialProtocolViolation('Datatype u_string has to be 6 characters long')
        for i in range(0, len(payload)):
            if (ord(payload[i]) < 0x20):
                raise SerialProtocolViolation('Invalid ASCII character in u_string payload '+payload)
        return payload

    def decodeDataType_5(self, payload):
        raise SerialProtocolViolation('Not implemented (ToDo)')

    def decodeDataType_6(self, payload):
        if len(payload) != 1:
            raise SerialProtocolViolation('Datatype boolean_new has to be 1 character long')
        if payload == '1':
            return True
        if payload == '0':
            return False
        raise SerialProtocolViolation('Invalid boolean_new value '+payload)

    def decodeDataType_7(self, payload):
        if len(payload) != 3:
            raise SerialProtocolViolation('Datatype u_short_int has to be 3 character long')
        try:
            num = int(payload)
        except Exception:
            raise SerialProtocolViolation('Cannot interpret u_short_int '+payload)
        return num

    def decodeDataType_9(self, payload):
        if len(payload) != 6:
            raise SerialProtocolViolation('Datatype tms_old has to be 6 character long')
        onoff = payload[:3]
        temp = payload[3:]
        if onoff == '111':
            onoff = True
        elif onoff == '000':
            onoff = False
        else:
            raise SerialProtocolViolation('Boolean value in tms_old has invalid value '+onoff)

        try:
            temp = int(temp)
        except Exception:
            raise SerialProtocolViolation('Signalled temperature in tms_old has non integer value '+temp)

        return {
            "onoff" : onoff,
            "temp" : temp
        }

    def decodeDataType_10(self, payload):
        if len(payload) != 6:
            raise SerialProtocolViolation('Datatype u_expo_new has to be 6 character long')
        try:
            mantissa = int(payload[:4])
            exponent = int(payload[-2:])
            mantissa = float(mantissa) / 1000.0
            return mantissa * pow(10, exponent)
        except Exception:
            raise SerialProtocolViolation('Mantissa or exponent in u_expo_new has invalid value '+payload)

    def decodeDataType_11(self, payload):
        if len(payload) != 16:
            raise SerialProtocolViolation('Datatype string16 has to be 16 character long')
        for i in range(0, len(payload)):
            if (ord(payload[i]) < 0x20):
                raise SerialProtocolViolation('Invalid ASCII character in string16 payload '+payload)
        return payload

    def decodeDataType_12(self, payload):
        if len(payload) != 8:
            raise SerialProtocolViolation('Datatype string8 has to be 8 character long')
        for i in range(0, len(payload)):
            if (ord(payload[i]) < 0x20):
                raise SerialProtocolViolation('Invalid ASCII character in string8 payload '+payload)
        return payload

    def decodeDataType_default(self, payload):
        raise SerialProtocolViolation('Unknown datatype specified for decoding')

    decodeDataType_Dictionary = {
        0   :   "decodeDataType_0",
        1   :   "decodeDataType_1",
        2   :   "decodeDataType_2",
        3   :   "decodeDataType_3",
        4   :   "decodeDataType_4",
        5   :   "decodeDataType_5",
        6   :   "decodeDataType_6",
        7   :   "decodeDataType_7",
        9   :   "decodeDataType_9",
        10  :   "decodeDataType_10",
        11  :   "decodeDataType_11",
        12  :   "decodeDataType_12"
    }

    def decodeDataType(self, payload, datatype):
        fun = self.decodeDataType_Dictionary.get(datatype, self.decodeDataType_default)
        return getattr(self, fun)(payload)

    def encodeDataType_0(self, payload):
        if not isinstance(payload, bool):
            raise SerialProtocolViolation("Trying to encode non boolean {} into bool boolean_old type".format(payload))
        if payload == True:
            return '111111'
        else:
            return '000000'

    def encodeDataType_1(self, payload):
        if not isinstance(payload, int):
            raise SerialProtocolViolation("Trying to encode non positive integer {} into u_integer type".format(payload))
        if payload < 0:
            raise SerialProtocolViolation("Trying to encode non positive integer {} into u_integer type".format(payload))
        return '{:06d}'.format(payload)

    def encodeDataType_2(self, payload):
        if not isinstance(payload, (int, float)):
            raise SerialProtocolViolation("Trying to encode non positive floating point value {} into u_real type".format(payload))
        if payload < 0:
            raise SerialProtocolViolation("Trying to encode non positive floating point value {} into u_real type".format(payload))
        return '{:06d}'.format(int(payload * 100.0))

    def encodeDataType_default(self, payload):
        raise SerialProtocolViolation("Data type not supported for encoding")

    encodeDataType_Dictionary = {
        0   :   "encodeDataType_0",
        1   :   "encodeDataType_1",
        2   :   "encodeDataType_2"
        # 3   :   "encodeDataType_3",
        # 4   :   "encodeDataType_4",
        # 5   :   "encodeDataType_5",
        # 6   :   "encodeDataType_6",
        # 7   :   "encodeDataType_7",
        # 9   :   "encodeDataType_9",
        # 10  :   "encodeDataType_10",
        # 11  :   "encodeDataType_11",
        # 12  :   "encodeDataType_12"
    }

    def encodeDataType(self, payload, datatype):
        fun = self.encodeDataType_Dictionary.get(datatype, self.encodeDataType_default)
        return getattr(self, fun)(payload)

    def decodePacket(self, packet, sentenceDictionary):
        if not (("address" in packet) or ("action" in packet) or ("param" in packet) or ("payloadLength" in packet) or ("payloadRaw" in packet)):
            raise SerialProtocolViolation("Packet passed does not contain information about a received serial protocol")

        regParam = int(packet["param"])
        if not regParam in sentenceDictionary:
            raise SerialProtocolUnknownRegister("Unknown register {} in packet".format(regParam))

        if packet["action"] == 1:
            packet["payload"]   = self.decodeDataType(packet["payloadRaw"], sentenceDictionary[regParam]["datatype"])
        else:
            packet["payload"]   = "=?"
        packet["designation"]   = sentenceDictionary[regParam]["designation"]
        packet["displayreg"]    = sentenceDictionary[regParam]["display"]
        packet["regaccess"]     = sentenceDictionary[regParam]["access"]
        packet["regunit"]       = sentenceDictionary[regParam]["unit"]
        packet["regmin"]        = sentenceDictionary[regParam]["min"]
        packet["regmax"]        = sentenceDictionary[regParam]["max"]
        packet["regdefault"]    = sentenceDictionary[regParam]["default"]
        packet["regpersistent"] = sentenceDictionary[regParam]["persistent"]

        return packet

    def encodePacket(self, targetAddress, action, regParam, value, sentenceDictionary, checkWritable = True):
        # This function validates the passed value and creates an encoded packet
        if not regParam in sentenceDictionary:
            raise SerialProtocolViolation("Unknown register {} in dictionary".format(regParam))

        if isinstance(value, (int, float)):
            if sentenceDictionary[regParam]["min"] != None:
                if value < sentenceDictionary[regParam]["min"]:
                    raise SerialProtocolViolation("Parameter {} has minimum value of {} but {} supplied".format(regParam, sentenceDictionary[regParam]["min"], value))
            if sentenceDictionary[regParam]["max"] != None:
                if value > sentenceDictionary[regParam]["max"]:
                    raise SerialProtocolViolation("Parameter {} has maximum value of {} but {} supplied".format(regParam, sentenceDictionary[regParam]["max"], value))

        if checkWritable and (sentenceDictionary[regParam]["access"] != ACCESS_RW) and (sentenceDictionary[regParam]["access"] != ACCESS_W):
            raise SerialProtocolViolation("Parameter {} is not writable".format(regParam))

        # Try to encode the data ...
        packet                  = { }

        packet["address"]       = targetAddress
        packet["param"]         = regParam
        packet["action"]        = action

        packet["payloadRaw"]    = self.encodeDataType(value, sentenceDictionary[regParam]["datatype"])
        packet["payloadLength"] = len(packet["payloadRaw"])
        packet["payload"]       = value

        packet["designation"]   = sentenceDictionary[regParam]["designation"]
        packet["displayreg"]    = sentenceDictionary[regParam]["display"]
        packet["regaccess"]     = sentenceDictionary[regParam]["access"]
        packet["regunit"]       = sentenceDictionary[regParam]["unit"]
        packet["regmin"]        = sentenceDictionary[regParam]["min"]
        packet["regmax"]        = sentenceDictionary[regParam]["max"]
        packet["regdefault"]    = sentenceDictionary[regParam]["default"]
        packet["regpersistent"] = sentenceDictionary[regParam]["persistent"]

        # First just build the whole checksummed area
        packet["packetRaw"]     = "{:03d}{:1d}0{:03d}{:02d}{}".format(targetAddress, action, regParam, len(packet["payloadRaw"]), packet["payloadRaw"])

        # Calculate the checksum
        packet["packetRaw"]     = packet["packetRaw"] + "{:03d}".format(sum(bytearray(packet["packetRaw"].encode(encoding = "ASCII"))) % 256) + "\r"

        return packet

    ACCESS_R  = 0
    ACCESS_RW = 1
    ACCESS_W  = 2

    registers = {
        "TC110" : {
            # Control commands (0xx)
              1 : { "datatype" : 0,  "access" : ACCESS_RW, "display" : "Heating",     "designation" : "Heating",                                   "unit" : None,    "min" : 0,    "max" : 1,       "persistent" : True,  "default" : 0,    "valueDescriptions" : { 0 : "off", 1 : "on" } },
              2 : { "datatype" : 0,  "access" : ACCESS_RW, "display" : "Standby",     "designation" : "Standby",                                   "unit" : None,    "min" : 0,    "max" : 1,       "persistent" : True,  "default" : 0,    "valueDescriptions" : { 0 : "off", 1 : "on" } },
              4 : { "datatype" : 0,  "access" : ACCESS_RW, "display" : "RUTimeCtrl",  "designation" : "Run-up time control",                       "unit" : None,    "min" : 0,    "max" : 1,       "persistent" : True,  "default" : 1,    "valueDescriptions" : { 0 : "off", 1 : "on" } },
              9 : { "datatype" : 0,  "access" : ACCESS_W,  "display" : "ErrorAckn",   "designation" : "Error acknowledgement",                     "unit" : None,    "min" : 1,    "max" : 1,       "persistent" : False, "default" : None, "valueDescriptions" : { 1 : "Error acknowledgement" } },
             10 : { "datatype" : 0,  "access" : ACCESS_RW, "display" : "PumpgStatn",  "designation" : "Pumping station",                           "unit" : None,    "min" : 0,    "max" : 1,       "persistent" : True,  "default" : 0,    "valueDescriptions" : { 0 : "off", 1 : "on and error acknowledgement" } },
             12 : { "datatype" : 0,  "access" : ACCESS_RW, "display" : "EnableVent",  "designation" : "Enable venting",                            "unit" : None,    "min" : 0,    "max" : 1,       "persistent" : True,  "default" : 0,    "valueDescriptions" : { 0 : "no", 1 : "yes" } },
             17 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "CfgSpdSwPt",  "designation" : "Configuration rotation speed switchpoint",  "unit" : None,    "min" : 0,    "max" : 1,       "persistent" : True,  "default" : 0,    "valueDescriptions" : { 0 : "rotation speed switch point 1", 1 : "rotation speed switch points 1 and 2" } },
             19 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "Cfg DO2",     "designation" : "Configuration output DO2",                  "unit" : None,    "min" : 0,    "max" : 22,      "persistent" : True,  "default" : 1,    "valueDescriptions" : { 0 : "Rotation speed switch point reached", 1 : "no error", 2 : "error", 3 : "warning", 4 : "error and/or warning", 5 : "set rotation speed reached", 6 : "pump on", 7 : "pump accelerating", 8 : "pump decelerating", 9 : "always 0", 10 : "always 1", 11 : "remote priority active", 12 : "heating", 13 : "backing pump", 14 : "sealing gas", 15 : "pumping station", 16 : "pump rotates", 17 : "pump does not rotate", 19 : "pressure switch point 1 underrund", 20 : "pressure switch point 2 underrun", 21 : "fore-vacuum valve, delayed", 22 : "backing pump standby" } },
             23 : { "datatype" : 0,  "access" : ACCESS_RW, "display" : "MotorPump",   "designation" : "Motor pump",                                "unit" : None,    "min" : 0,    "max" : 1,       "persistent" : True,  "default" : 1,    "valueDescriptions" : { 0 : "off", 1 : "on" } },
             24 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "Cfg DO1",     "designation" : "Configuration output DO1",                  "unit" : None,    "min" : 0,    "max" : 22,      "persistent" : True,  "default" : 0,    "valueDescriptions" : { 0 : "Rotation speed switch point reached", 1 : "no error", 2 : "error", 3 : "warning", 4 : "error and/or warning", 5 : "set rotation speed reached", 6 : "pump on", 7 : "pump accelerating", 8 : "pump decelerating", 9 : "always 0", 10 : "always 1", 11 : "remote priority active", 12 : "heating", 13 : "backing pump", 14 : "sealing gas", 15 : "pumping station", 16 : "pump rotates", 17 : "pump does not rotate", 19 : "pressure switch point 1 underrund", 20 : "pressure switch point 2 underrun", 21 : "fore-vacuum valve, delayed", 22 : "backing pump standby" } },
             25 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "OpMode BKP",  "designation" : "Backing pump mode",                         "unit" : None,    "min" : 0,    "max" : 3,       "persistent" : True,  "default" : 0,    "valueDescriptions" : { 0 : "continuous operation", 1 : "intermittent operation", 2 : "delayed switching on", 3 : "delayed switching off" } },
             26 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "SpdSetMode",  "designation" : "Rotation speed setting mode",               "unit" : None,    "min" : 0,    "max" : 1,       "persistent" : True,  "default" : 0,    "valueDescriptions" : { 0 : "off", 1 : "on" } },
             27 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "GasMode",     "designation" : "Gas mode",                                  "unit" : None,    "min" : 0,    "max" : 2,       "persistent" : True,  "default" : 0,    "valueDescriptions" : { 0 : "heavy gases", 1 : "light gases", 2 : "Helium" } },
             30 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "VentMode",    "designation" : "Venting mode",                              "unit" : None,    "min" : 0,    "max" : 2,       "persistent" : True,  "default" : 0,    "valueDescriptions" : { 0 : "delayed venting", 1 : "no venting", 2 : "direct venting" } },
             35 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "Cfg Acc A1",  "designation" : "Configuration accessory connection A1",     "unit" : None,    "min" : 0,    "max" : 12,      "persistent" : True,  "default" : 0,    "valueDescriptions" : { 0 : "fan", 1 : "venting valve, closed without current", 2 : "heating", 3 : "backing pump", 4 : "fan (temperatuer controlled)", 5 : "sealing gas", 6 : "always 0", 7 : "always 1", 8 : "power failure venting unit", 9 : "TMS heating", 10 : "TMS cooling", 12 : "Second venting valve", 13 : "Sealing gas monitoring", 14 : "heating (bottom part temperature controlled)" } },
             36 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "Cfg Acc B1",  "designation" : "Configuration accessory connection B1",     "unit" : None,    "min" : 0,    "max" : 12,      "persistent" : True,  "default" : 1,    "valueDescriptions" : { 0 : "fan", 1 : "venting valve, closed without current", 2 : "heating", 3 : "backing pump", 4 : "fan (temperatuer controlled)", 5 : "sealing gas", 6 : "always 0", 7 : "always 1", 8 : "power failure venting unit", 9 : "TMS heating", 10 : "TMS cooling", 12 : "Second venting valve", 13 : "Sealing gas monitoring", 14 : "heating (bottom part temperature controlled)" } },
             37 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "Cfg Acc A2",  "designation" : "Configuration accessory connection B1",     "unit" : None,    "min" : 0,    "max" : 12,      "persistent" : True,  "default" : 3,    "valueDescriptions" : { 0 : "fan", 1 : "venting valve, closed without current", 2 : "heating", 3 : "backing pump", 4 : "fan (temperatuer controlled)", 5 : "sealing gas", 6 : "always 0", 7 : "always 1", 8 : "power failure venting unit", 9 : "TMS heating", 10 : "TMS cooling", 12 : "Second venting valve", 13 : "Sealing gas monitoring", 14 : "heating (bottom part temperature controlled)" } },
             38 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "Cfg Acc B2",  "designation" : "Configuration accessory connection B1",     "unit" : None,    "min" : 0,    "max" : 12,      "persistent" : True,  "default" : 2,    "valueDescriptions" : { 0 : "fan", 1 : "venting valve, closed without current", 2 : "heating", 3 : "backing pump", 4 : "fan (temperatuer controlled)", 5 : "sealing gas", 6 : "always 0", 7 : "always 1", 8 : "power failure venting unit", 9 : "TMS heating", 10 : "TMS cooling", 12 : "Second venting valve", 13 : "Sealing gas monitoring", 14 : "heating (bottom part temperature controlled)" } },
             41 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "Press1HVen",  "designation" : "Enable integrated HV sensor (IKT only)",    "unit" : None,    "min" : 0,    "max" : 3,       "persistent" : True,  "default" : 2,    "valueDescriptions" : { 0 : "off", 1 : "on", 2 : "on, when rotation speed switch point reached", 3 : "on when pressure switch point underrun" } },
             50 : { "datatype" : 0,  "access" : ACCESS_RW, "display" : "SealingGas",  "designation" : "Sealing gas",                               "unit" : None,    "min" : 0,    "max" : 1,       "persistent" : True,  "default" : 0,    "valueDescriptions" : { 0 : "off", 1 : "on" } },
             55 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "Cfg AO1",     "designation" : "Configurtation output AO1",                 "unit" : None,    "min" : 0,    "max" : 8,       "persistent" : True,  "default" : 0,    "valueDescriptions" : { 0 : "Actual rotation speed", 1 : "Output", 2 : "Current", 3 : "Always 0V", 4 : "Always 10V", 6 : "Pressure value 1", 7 : "Pressure value 2", 8 : "Fore-vacuum control" } },
             60 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "CtrlViaInt",  "designation" : "Control via Interface",                     "unit" : None,    "min" : 0,    "max" : 255,     "persistent" : True,  "default" : 1,    "valueDescriptions" : { 1 : "Remote", 2 : "RS-485", 4 : "PV.can", 8 : "Fieldbus", 16 : "E74", 255 : "Unlock interface selection" } },
             61 : { "datatype" : 0,  "access" : ACCESS_RW, "display" : "IntSelLckd",  "designation" : "Interface selection locked",                "unit" : None,    "min" : 1,    "max" : 1,       "persistent" : True,  "default" : 0,    "valueDescriptions" : { 0 : "off", 1 : "on" } },
             62 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "Cfg DI1",     "designation" : "Configuration input DI1",                   "unit" : None,    "min" : 0,    "max" : 7,       "persistent" : True,  "default" : 1,    "valueDescriptions" : { 0 : "deactivated" , 1 : "enable venting", 2 : "heating", 3 : "sealing gas", 4 : "run-up time monitoring", 5 : "rotation speed mode", 6 : "motor", 7 : "enable HV sensor 1" } },
             63 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "Cfg DI2",     "designation" : "Configuration input DI2",                   "unit" : None,    "min" : 0,    "max" : 7,       "persistent" : True,  "default" : 2,    "valueDescriptions" : { 0 : "deactivated" , 1 : "enable venting", 2 : "heating", 3 : "sealing gas", 4 : "run-up time monitoring", 5 : "rotation speed mode", 6 : "motor", 7 : "enable HV sensor 1" } },

            # Status requests (3xx)
            300 : { "datatype" : 0,  "access" : ACCESS_R,  "display" : "RemotePrio",  "designation" : "Remote priority",                           "unit" : None,    "min" : 0,    "max" : 1,       "persistent" : False, "default" : None, "valueDescriptions" : { 0 : "no", 1 : "yes" } },
            302 : { "datatype" : 0,  "access" : ACCESS_R,  "display" : "SpdSwPtAtt",  "designation" : "Rotation speed switchpoint attained",       "unit" : None,    "min" : 0,    "max" : 1,       "persistent" : False, "default" : None, "valueDescriptions" : { 0 : "no", 1 : "yes" } },
            303 : { "datatype" : 4,  "access" : ACCESS_R,  "display" : "Error code",  "designation" : "Error code",                                "unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            304 : { "datatype" : 0,  "access" : ACCESS_R,  "display" : "OvTempElec",  "designation" : "Excess temperature electronic drive unit",  "unit" : None,    "min" : 0,    "max" : 1,       "persistent" : False, "default" : None, "valueDescriptions" : { 0 : "no", 1 : "yes" } },
            305 : { "datatype" : 0,  "access" : ACCESS_R,  "display" : "OvTempPump",  "designation" : "Excess temperature pump",                   "unit" : None,    "min" : 0,    "max" : 1,       "persistent" : False, "default" : None, "valueDescriptions" : { 0 : "no", 1 : "yes" } },
            306 : { "datatype" : 0,  "access" : ACCESS_R,  "display" : "SetSpdAtt",   "designation" : "Set rotation speed attained",               "unit" : None,    "min" : 0,    "max" : 1,       "persistent" : False, "default" : None, "valueDescriptions" : { 0 : "no", 1 : "yes" } },
            307 : { "datatype" : 0,  "access" : ACCESS_R,  "display" : "PumpAccel",   "designation" : "Pump accelerates",                          "unit" : None,    "min" : 0,    "max" : 1,       "persistent" : False, "default" : None, "valueDescriptions" : { 0 : "no", 1 : "yes" } },
            308 : { "datatype" : 1,  "access" : ACCESS_R,  "display" : "SetRotSpd",   "designation" : "Set rotation speed",                        "unit" : "Hz",    "min" : 0,    "max" : 999999,  "persistent" : False, "default" : None, "valueDescriptions" : None },
            309 : { "datatype" : 1,  "access" : ACCESS_R,  "display" : "ActualSpd",   "designation" : "Active rotation speed",                     "unit" : "Hz",    "min" : 0,    "max" : 999999,  "persistent" : False, "default" : None, "valueDescriptions" : None },
            310 : { "datatype" : 2,  "access" : ACCESS_R,  "display" : "DrvCurrent",  "designation" : "Drive current",                             "unit" : "A",     "min" : 0,    "max" : 9999.99, "persistent" : False, "default" : None, "valueDescriptions" : None },
            311 : { "datatype" : 1,  "access" : ACCESS_R,  "display" : "OpHrsPump",   "designation" : "Operating hours pump",                      "unit" : "h",     "min" : 0,    "max" : 65535,   "persistent" : True,  "default" : None, "valueDescriptions" : None },
            312 : { "datatype" : 4,  "access" : ACCESS_R,  "display" : "Fw version",  "designation" : "Firmware version electronic drive unit",    "unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            313 : { "datatype" : 2,  "access" : ACCESS_R,  "display" : "DrvVoltage",  "designation" : "Drive voltage",                             "unit" : "V",     "min" : 0,    "max" : 9999.99, "persistent" : False, "default" : None, "valueDescriptions" : None },
            314 : { "datatype" : 1,  "access" : ACCESS_R,  "display" : "OpHrsElec",   "designation" : "Operating hours pump",                      "unit" : "h",     "min" : 0,    "max" : 65535,   "persistent" : True,  "default" : None, "valueDescriptions" : None },
            315 : { "datatype" : 1,  "access" : ACCESS_R,  "display" : "Nominal Spd", "designation" : "Nominal rotation speed",                    "unit" : "Hz",    "min" : 0,    "max" : 999999,  "persistent" : False, "default" : None, "valueDescriptions" : None },
            316 : { "datatype" : 1,  "access" : ACCESS_R,  "display" : "DrvPower",    "designation" : "Drive power",                               "unit" : "W",     "min" : 0,    "max" : 999999,  "persistent" : False, "default" : None, "valueDescriptions" : None },
            319 : { "datatype" : 1,  "access" : ACCESS_R,  "display" : "PumpCycles",  "designation" : "Pump cycles",                               "unit" : None,    "min" : 0,    "max" : 65535,   "persistent" : True,  "default" : None, "valueDescriptions" : None },
            326 : { "datatype" : 1,  "access" : ACCESS_R,  "display" : "TempElec",    "designation" : "Temperature electronic",                    "unit" : "C",     "min" : 0,    "max" : 999999,  "persistent" : False, "default" : None, "valueDescriptions" : None },
            330 : { "datatype" : 1,  "access" : ACCESS_R,  "display" : "TempPmpBot",  "designation" : "Temperature pump bottom part",              "unit" : "C" ,    "min" : 0,    "max" : 999999,  "persistent" : False, "default" : None, "valueDescriptions" : None },
            336 : { "datatype" : 1,  "access" : ACCESS_R,  "display" : "AccelDecel",  "designation" : "Acceleration / Deceleration",               "unit" : "rpm/s", "min" : 0,    "max" : 999999,  "persistent" : False, "default" : None, "valueDescriptions" : None },
            342 : { "datatype" : 1,  "access" : ACCESS_R,  "display" : "TempBearng",  "designation" : "Temperature bearing",                       "unit" : "C",     "min" : 0,    "max" : 999999,  "persistent" : False, "default" : None, "valueDescriptions" : None },
            346 : { "datatype" : 1,  "access" : ACCESS_R,  "display" : "TempMotor",   "designation" : "Temperature motor",                         "unit" : "C",     "min" : 0,    "max" : 999999,  "persistent" : False, "default" : None, "valueDescriptions" : None },
            349 : { "datatype" : 4,  "access" : ACCESS_R,  "display" : "ElecName",    "designation" : "Name of electronic drive unit",             "unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            354 : { "datatype" : 4,  "access" : ACCESS_R,  "display" : "HwVersion",   "designation" : "Hardware version electronic drive unit",    "unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            360 : { "datatype" : 4,  "access" : ACCESS_R,  "display" : "ErrHist1",    "designation" : "Error code history, position 1",            "unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            361 : { "datatype" : 4,  "access" : ACCESS_R,  "display" : "ErrHist2",    "designation" : "Error code history, position 2",            "unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            362 : { "datatype" : 4,  "access" : ACCESS_R,  "display" : "ErrHist3",    "designation" : "Error code history, position 3",            "unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            363 : { "datatype" : 4,  "access" : ACCESS_R,  "display" : "ErrHist4",    "designation" : "Error code history, position 4",            "unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            364 : { "datatype" : 4,  "access" : ACCESS_R,  "display" : "ErrHist5",    "designation" : "Error code history, position 5",            "unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            365 : { "datatype" : 4,  "access" : ACCESS_R,  "display" : "ErrHist6",    "designation" : "Error code history, position 6",            "unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            366 : { "datatype" : 4,  "access" : ACCESS_R,  "display" : "ErrHist7",    "designation" : "Error code history, position 7",            "unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            367 : { "datatype" : 4,  "access" : ACCESS_R,  "display" : "ErrHist8",    "designation" : "Error code history, position 8",            "unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            368 : { "datatype" : 4,  "access" : ACCESS_R,  "display" : "ErrHist9",    "designation" : "Error code history, position 9",            "unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            369 : { "datatype" : 4,  "access" : ACCESS_R,  "display" : "ErrHist10",   "designation" : "Error code history, position 10",           "unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            397 : { "datatype" : 1,  "access" : ACCESS_R,  "display" : "SetRotSpd",   "designation" : "Set rotation speed",                        "unit" : "rpm",   "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            398 : { "datatype" : 1,  "access" : ACCESS_R,  "display" : "ActualSpd",   "designation" : "Actual rotation speed",                     "unit" : "rpm",   "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            399 : { "datatype" : 1,  "access" : ACCESS_R,  "display" : "NominalSpd",  "designation" : "Nominal rotation speed",                    "unit" : "rpm",   "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },

            # Set value settings (7xx)
            700 : { "datatype" : 1,  "access" : ACCESS_RW, "display" : "RUTimeSVal",  "designation" : "Set value run-up time",                     "unit" : "min",   "min" : 1,    "max" : 120,     "persistent" : True,  "default" : 8   , "valueDescriptions" : None },
            701 : { "datatype" : 1,  "access" : ACCESS_RW, "display" : "SPdSwPt1",    "designation" : "Rotation speed switchpoint 1",              "unit" : "%",     "min" : 50,   "max" : 97,      "persistent" : True,  "default" : 80  , "valueDescriptions" : None },
            707 : { "datatype" : 2,  "access" : ACCESS_RW, "display" : "SpdSVal",     "designation" : "Set value in rotation speed setting mode",  "unit" : "%",     "min" : 20,   "max" : 100,     "persistent" : True,  "default" : 65  , "valueDescriptions" : None },
            708 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "PwrSVal",     "designation" : "Set value power consumption",               "unit" : "%",     "min" : 0,    "max" : 100,     "persistent" : True,  "default" : 100 , "valueDescriptions" : None },
            710 : { "datatype" : 1,  "access" : ACCESS_RW, "display" : "Swoff BKP",   "designation" : "Switching off threshold for backing pump",  "unit" : "W",     "min" : 0,    "max" : 1000,    "persistent" : True,  "default" : 0   , "valueDescriptions" : None },
            711 : { "datatype" : 1,  "access" : ACCESS_RW, "display" : "Swon BKP",    "designation" : "Switching on threshold for backing pump",   "unit" : "W",     "min" : 0,    "max" : 1000,    "persistent" : True,  "default" : 0   , "valueDescriptions" : None },
            717 : { "datatype" : 2,  "access" : ACCESS_RW, "display" : "StdbySVal",   "designation" : "Set value rotation speed at standby",       "unit" : "%",     "min" : 20,   "max" : 100,     "persistent" : True,  "default" : 66.7, "valueDescriptions" : None },
            719 : { "datatype" : 1,  "access" : ACCESS_RW, "display" : "SpdSwPt2",    "designation" : "Rotation speed switchpoint 2",              "unit" : "%",     "min" : 5,    "max" : 97,      "persistent" : True,  "default" : 20  , "valueDescriptions" : None },
            720 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "VentSpd",     "designation" : "Venting rotation speed at delayed venting", "unit" : "%",     "min" : 40,   "max" : 98,      "persistent" : True,  "default" : 50  , "valueDescriptions" : None },
            721 : { "datatype" : 1,  "access" : ACCESS_RW, "display" : "VentTime",    "designation" : "Venting time at delayed venting",           "unit" : "s",     "min" : 6,    "max" : 3600,    "persistent" : True,  "default" : 3600, "valueDescriptions" : None },
            730 : { "datatype" : 10, "access" : ACCESS_RW, "display" : "PrsSwPt 1",   "designation" : "Pressure switchpoint 1",                    "unit" : "hPa",   "min" : None, "max" : None,    "persistent" : True,  "default" : None, "valueDescriptions" : None },
            732 : { "datatype" : 10, "access" : ACCESS_RW, "display" : "PrsSwPt 2",   "designation" : "Pressure switchpoint 2",                    "unit" : "hPa",   "min" : None, "max" : None,    "persistent" : True,  "default" : None, "valueDescriptions" : None },
            739 : { "datatype" : 4,  "access" : ACCESS_R,  "display" : "PrsSn1Name",  "designation" : "Pressure sensor 1 name",                    "unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            740 : { "datatype" : 10, "access" : ACCESS_RW, "display" : "Pressure 1",  "designation" : "Pressure value 1",                          "unit" : "hPa",   "min" : None, "max" : None,    "persistent" : True,  "default" : None, "valueDescriptions" : None },
            742 : { "datatype" : 2,  "access" : ACCESS_RW, "display" : "PrsCorrPi 1", "designation" : "Pressure correction factor 1",              "unit" : None,    "min" : None, "max" : None,    "persistent" : True,  "default" : None, "valueDescriptions" : None },
            749 : { "datatype" : 4,  "access" : ACCESS_R,  "display" : "PrsSn2Name",  "designation" : "Pressure sensor 2 name",                    "unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            750 : { "datatype" : 10, "access" : ACCESS_RW, "display" : "Pressure 2",  "designation" : "Pressure value 2",                          "unit" : "hPa",   "min" : None, "max" : None,    "persistent" : True,  "default" : None, "valueDescriptions" : None },
            752 : { "datatype" : 2,  "access" : ACCESS_RW, "display" : "PrsCorrPi2",  "designation" : "Pressure correction factor 2",              "unit" : None,    "min" : None, "max" : None,    "persistent" : True,  "default" : None, "valueDescriptions" : None },
            777 : { "datatype" : 1,  "access" : ACCESS_RW, "display" : "NomSpdConf",  "designation" : "Nomial rotation speed confirmation",        "unit" : "Hz",    "min" : 0,    "max" : 1500,    "persistent" : True,  "default" : 0   , "valueDescriptions" : None },
            797 : { "datatype" : 1,  "access" : ACCESS_RW, "display" : "RS485Adr",    "designation" : "RS-485 device address",                     "unit" : None,    "min" : 1,    "max" : 255,     "persistent" : True,  "default" : 1   , "valueDescriptions" : None },

            # Additional values for DCU
            340 : { "datatype" : 7,  "access" : ACCESS_R,  "display" : "Pressure",    "designation" : "Actual pressure value (ActiveLine)",        "unit" : "hPa",   "min" : 1e-10, "max" : 1e3,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            350 : { "datatype" : 4,  "access" : ACCESS_R,  "display" : "Ctr Name",    "designation" : "Display and control panel type",            "unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            351 : { "datatype" : 4,  "access" : ACCESS_R,  "display" : "Ctr Software","designation" : "Display and control panel software version","unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            738 : { "datatype" : 4,  "access" : ACCESS_RW, "display" : "Gauge type",  "designation" : "Type of pressure gauge",                    "unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            794 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "Param set",   "designation" : "Parameter set",                             "unit" : None,    "min" : 0,    "max" : 1,       "persistent" : False, "default" : 0,    "valueDescriptions" : { 0 : "Basic parameter set", 1 : "Extended parameter set" } },
            795 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "Servicelin",  "designation" : "Insert service line",                       "unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : 795,  "valueDescriptions" : None }
        },
        "MVP015" : {
              2 : { "datatype" : 0,  "access" : ACCESS_RW, "display" : "Standby",     "designation" : "Standby",                                   "unit" : None,    "min" : 0,    "max" : 1,       "persistent" : True,  "default" : 0   , "valueDescriptions" : None },
              9 : { "datatype" : 0,  "access" : ACCESS_W,  "display" : "ErrorAckn",   "designation" : "Fault acknowledgement",                     "unit" : None,    "min" : 1,    "max" : 1,       "persistent" : False, "default" : None, "valueDescriptions" : None },
             10 : { "datatype" : 0,  "access" : ACCESS_RW, "display" : "PumpgStatn",  "designation" : "Pump",                                      "unit" : None,    "min" : 0,    "max" : 1,       "persistent" : True,  "default" : 0   , "valueDescriptions" : None },
             19 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "Cfg DO2",     "designation" : "Configuration output DO2",                  "unit" : None,    "min" : 0,    "max" : 20,      "persistent" : True,  "default" : 5   , "valueDescriptions" : None },
             24 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "Cfg DO1",     "designation" : "Configuration output DO1",                  "unit" : None,    "min" : 0,    "max" : 20,      "persistent" : True,  "default" : 1   , "valueDescriptions" : None },
             26 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "SpdSetMode",  "designation" : "Speed setting mode",                        "unit" : None,    "min" : 0,    "max" : 1,       "persistent" : True,  "default" : 0   , "valueDescriptions" : None },
             30 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "ValveMode",   "designation" : "Purge gas configuration",                   "unit" : None,    "min" : 0,    "max" : 2,       "persistent" : True,  "default" : 0   , "valueDescriptions" : None },
             50 : { "datatype" : 0,  "access" : ACCESS_RW, "display" : "PurgeGas",    "designation" : "Purge gas",                                 "unit" : None,    "min" : 0,    "max" : 1,       "persistent" : True,  "default" : 0   , "valueDescriptions" : None },
             60 : { "datatype" : 7,  "access" : ACCESS_RW, "display" : "CtrlViaInt",  "designation" : "Control via interface",                     "unit" : None,    "min" : 0,    "max" : 255,     "persistent" : True,  "default" : 1   , "valueDescriptions" : None },
             61 : { "datatype" : 0,  "access" : ACCESS_RW, "display" : "IntSelLckd",  "designation" : "Interface selection locked",                "unit" : None,    "min" : 0,    "max" : 1,       "persistent" : True,  "default" : 0   , "valueDescriptions" : None },

            303 : { "datatype" : 4,  "access" : ACCESS_R,  "display" : "Error code",  "designation" : "Error code",                                "unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            309 : { "datatype" : 1,  "access" : ACCESS_R,  "display" : "ActualSpd",   "designation" : "Actual speed",                              "unit" : "Hz",    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            310 : { "datatype" : 2,  "access" : ACCESS_R,  "display" : "DrvCurrent",  "designation" : "Drive current",                             "unit" : "A",     "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            311 : { "datatype" : 1,  "access" : ACCESS_R,  "display" : "OpHrsPump",   "designation" : "Pump operating hours",                      "unit" : "h",     "min" : None, "max" : None,    "persistent" : True,  "default" : None, "valueDescriptions" : None },
            312 : { "datatype" : 4,  "access" : ACCESS_R,  "display" : "Fw version",  "designation" : "Software version of the interface board",   "unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            313 : { "datatype" : 2,  "access" : ACCESS_R,  "display" : "DrvVoltage",  "designation" : "Supply voltage",                            "unit" : "V",     "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            314 : { "datatype" : 1,  "access" : ACCESS_R,  "display" : "OpHrsElec",   "designation" : "Electronic drive unit operating hours",     "unit" : "h",     "min" : None, "max" : None,    "persistent" : True,  "default" : None, "valueDescriptions" : None },
            315 : { "datatype" : 1,  "access" : ACCESS_R,  "display" : "Nominal Spd", "designation" : "Nominal speed",                             "unit" : "Hz",    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            316 : { "datatype" : 1,  "access" : ACCESS_R,  "display" : "DrvPower",    "designation" : "Drive power",                               "unit" : "W",     "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            330 : { "datatype" : 1,  "access" : ACCESS_R,  "display" : "TempPmpBot",  "designation" : "Temperature of pump",                       "unit" : "C",     "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            349 : { "datatype" : 4,  "access" : ACCESS_R,  "display" : "ElecName",    "designation" : "Device designation",                        "unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            398 : { "datatype" : 4,  "access" : ACCESS_R,  "display" : "HW version",  "designation" : "Hardware version of the interface board",   "unit" : None,    "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            354 : { "datatype" : 1,  "access" : ACCESS_R,  "display" : "ActualSpd",   "designation" : "Actual speed",                              "unit" : "rpm",   "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },
            399 : { "datatype" : 1,  "access" : ACCESS_R,  "display" : "NominalSpd",  "designation" : "Nominal speed",                             "unit" : "rpm",   "min" : None, "max" : None,    "persistent" : False, "default" : None, "valueDescriptions" : None },

            707 : { "datatype" : 2,  "access" : ACCESS_RW, "display" : "SpdSVal",     "designation" : "Setpoint in speed setting mode",            "unit" : "%",     "min" : 30, "max" : 170,       "persistent" : True,  "default" : 75  , "valueDescriptions" : None },
            717 : { "datatype" : 2,  "access" : ACCESS_RW, "display" : "StdbySVal",   "designation" : "Setpoint speed in standby mode",            "unit" : "%",     "min" : 30, "max" : 100,       "persistent" : True,  "default" : 66.7, "valueDescriptions" : None },
            721 : { "datatype" : 1,  "access" : ACCESS_RW, "display" : "SlgVlvTime",  "designation" : "Setting for purge gas active",              "unit" : "s",     "min" : 5, "max" : 255,        "persistent" : True,  "default" : 60  , "valueDescriptions" : None },
            797 : { "datatype" : 1,  "access" : ACCESS_RW, "display" : "RS485Adr",    "designation" : "RS485 interface address",                   "unit" : None,    "min" : 1, "max" : 255,        "persistent" : True,  "default" : 2   , "valueDescriptions" : None }
        }
    }
