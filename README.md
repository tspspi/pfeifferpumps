# Unofficial control library and CLI utility for Pfeiffer turbopumps

This is a simple _unofficial_ (it's in no way associated with Pfeiffer vaccuum
or any of their partners) Python library and utility collection to work with
Pfeiffer turbopumps via the RS485 interface.

__WARNING: WORK IN PROGRESS!!__. This project is _not_ generally usable in it's
current state and there are currently some decoding errors (or capture problems)
with many status messages queried during startup.

Currently available components:

* ```PfeifferProtocol``` is a simple serialization and deserialization library
  that creates and parses the RS485 on wire messages. It also allows to add
  metadata for supported devices (register maps are keps in dictionaries inside
  the class) and parses the raw payload accordingly.
* ```PfeifferRS485Serial``` handles the RS485 bus via a simple RS232 <-> TTL
  converter and MAX485 RS485 driver. This can be used in sniffer, master or
  slave mode. Sniffer mode is used to watch the communication between a master
  like the DCU and the attached components, master mode allows one to implement
  an own control unit and slave mode allows one to emulate various devices for
  testing purposes.

Currently available utilities:

* ```pfeiffersniff``` is a simple command line utility that exposes core features
  of the libraries via the CLI to allow simple and easy monitoring of the bus
  and optionally controlling the attached pumps.

## Supported devices

| Type                 | Name   | Support / Comment                            |
| -------------------- | ------ | -------------------------------------------- |
| Turbopump controller | TC110  | Decoder for documented registers implemented |
| Membrane pump        | MVP015 | Decoder for documented registers implemented |

## The protocol library

The protocol library is implemented in ```pfeifferproto.py```. It can simply be
imported using

```
from pfeifferpumps.pfeifferproto import PfeifferProtocol, SerialProtocolViolation, SerialProtocolUnknownRegister
```

### Decoding ASCII packets

Routines for decoding ASCII packets are usually used by the library internally
to decode packets received on the serial interface - in case a device type
has been specified the registerset definition can be used to further decode
and interpret the values. In case one wants to do this by oneself
there are two routines to decode packets that have been captured as ASCII
lines - for example in the format ```'0011030906015000026\r'```. The first
one simply decodes the packet, verifies the checksum and builds a basic
packet dictionary but does not interpret it's payload:

```
with PfeifferProtocol() as proto:
    result = proto.decodePacketRaw('0011030906015000026\r')
```

This would create an object with the following structure:

```
{
    'address': 1,
    'param': 309,
    'action': 1,
    'payloadRaw': '015000',
    'payloadLength': 6,
    'packetRaw': '0011030906015000026\r'
}
```

No data has been interpreted.

A ```SerialProtocolViolation``` is thrown in case:

* The message is too short
* The message is not correctly terminated by ```'\r'```
* The message is malformed
* The checksum is invalid

To further decode the message one has to know the registerset. These are kept
in the dictionary ```registers``` inside the ```PfeifferProtocol``` class as
a dictionary mapping the device types to register definitions. For
example ```registers["TC110"]``` would be the registerset definition for
the TC110 turbopump controller. To further decode a previously decoded raw
packet one can use ```decodePacket(packet, sentenceDictionary)```:

```
with PfeifferProtocol() as proto:
    packet = proto.decodePacketRaw('0011030906015000026\r')
    packet = proto.decodePacket(packet, proto.registers["TC110"])
```

This would yield a dictionary describing the packet:

```
{
    'address': 1,
    'param': 309,
    'action': 1,
    'payloadRaw': '015000',
    'payloadLength': 6,
    'packetRaw': '0011030906015000026\r',
    'payload': 15000,
    'designation': 'Active rotation speed',
    'displayreg': 'ActualSpd',
    'regaccess': 0,
    'regunit': 'Hz',
    'regmin': 0,
    'regmax': 999999,
    'regdefault': None,
    'regpersistent': False
}
```

As one can see the method decodes the raw payload into the specific datatype (in
this exampel into an integer) and performs validations on the value - it checks
if the value is in range, if the encodings are valid, etc. In addition
it adds:

* The ```displayreg``` attribute that indicates what would be displayed on the
  DCU LCD
* The ```designation``` that includes a description of the register
* In case it's available the unit (```regunit```) - as well as allowed
  definition set (```regmin``` and ```regmax```) for numerical values.
* It indicates an optional default value (```regdefault```)
* The ```regpersistent``` flag tells if this register will be stored during
  a power cycle in persistent storage of the given control unit.
* The ```regaccess``` field tells if access to the register is allowed
  read only (```PfeifferProtocol.ACCESS_R```), in read/write mode (```PfeifferProtocol.ACCESS_RW```)
  or write only (```PfeifferProtocol.ACCESS_W```)
* The fields ```address```, ```param```, ```action```, ```payloadRaw``` and ```payloadLength```
  as well as ```packetRaw``` are copied from the raw packet structure

### Encoding messages

The protocol library supports a single encoding function that is able to
create a protocol message:

```
encodePacket(targetAddress, action, regParam, value, sentenceDictionary, checkWritable = True)
```

Arguments:

* ```targetAddress``` is the RS485 destination address of the packet
* ```action``` can be either a read request (0) or a write or response to a
  read request (1).
* ```regParam``` selects the register that one targets
* ```value``` is the value that one wants to write into the given register or
  report from the given register. This is encoded in it's native corresponding
  datatype (int, string, float, etc.)
* The ```sentenceDictionary``` selects the registerset that should be used
* When using ```checkWritable``` set to ```True``` the function will only allow
  one to create packets targeting writable registers, when set to ```False``` one
  can encode every packet.

For example the counterpart to the decode example would look like the following:

```
with PfeifferProtocol() as proto:
    packet = proto.encodePacket(1, 1, 309, 15000, proto.registers["TC110"], checkWritable = False)
```

This function always has to be supplied with a dictionary - the example would
create a simple packet:

```
{
    'address': 1,
    'param': 309,
    'action': 1,
    'payloadRaw': '015000',
    'payloadLength': 6,
    'payload': 15000,
    'designation': 'Active rotation speed',
    'displayreg': 'ActualSpd',
    'regaccess': 0,
    'regunit': 'Hz',
    'regmin': 0,
    'regmax': 999999,
    'regdefault': None,
    'regpersistent': False,
    'packetRaw': '0011030906015000026\r'
}
```

As one can see the format matches the decoding / parsing format and also includes
the on wire representation as ```packetRaw```

## The RS485 serial port library

The ```PfeifferRS485Serial``` class allows one to access pumps and devices on
an RS485 bus that's attached via a simple RS232 to RS485 serial bridge. This
can easily be built using readily available [CP2102 TTL to USB](https://amzn.to/30aAa56)
adapters and an [MAX485 breakout board](https://amzn.to/3BzgSV2) though for a
simple sniffer one should remove the termination resistor.

To create a connection one can again use the ```with``` construct:

```
from pfeifferpumps.pfeifferrs485 import PfeifferRS485Serial

try:
    with PfeifferRS485Serial(portFile, { 1 : "TC110" }) as port:
        while True:
            nextMsg = port.nextMessage()
            print(nextMsg)
except serial.SerialException as e:
    print("Failed to connect to serial port {}".format(portFile))
except SerialProtocolViolation as e:
    print(e)
except SerialCommunicationError as e:
    print(e)
except KeyboardInterrupt:
    print("\r", end="")
    print("Exiting ...")
```

As one can see the first argument to the ```PfeifferRS485Serial``` constructor
specifies the port name or port file name (such as ```/dev/ttyU0``` - which is
by coincidence also the default value). The second argument allows one to
specify the devices type / select the register sets for different devices on
the bus that should be handled while decoding and encoding messages. In case
one has a ```TC110``` on address 1 and ```DCU110``` on address 0 one could simply
supply the following dictionary:

```
{
    1 : "TC110",
    0 : "DCU110"
}
```

The library will then locate the given registerset from the protocol library
or raise an ```SerialProtocolViolation``` in case the device is not supported.

As one can see from the sample the ```nextMessage()``` routine can be used
to block for the next message on the bus and return the decoded message as
soon as it has been received.

The packet returned by ```nextMessage``` looks like the one returned by
the decode functions - depending if one has configured a registerset for the
given device address or not. In addition all packets are timestamped with
a human readable timestamp (```time```) and the unix epoch (```timestamp```):

```
{
    'address': 1,
    'param': 309,
    'action': 1,
    'payloadRaw': '015000',
    'payloadLength': 6,
    'packetRaw': '0011030906015000026\r',
    'payload': 15000,
    'designation': 'Active rotation speed',
    'displayreg': 'ActualSpd',
    'regaccess': 0,
    'regunit': 'Hz',
    'regmin': 0,
    'regmax': 999999,
    'regdefault': None,
    'regpersistent': False,
    'time': '2021-10-15 07:00:00.630690',
    'timestamp': 1634274000
}
```

## The CLI tool

### The sniffer

The protocol sniffer allows one to tap into the RS485 bus and log as well as
decode all encountered messages. It dumps all encountered messages as well
as any errors onto the standard output. In addition it allows logging into
a JSON dump (and is also capable of replaying using the same dump with different
configurations again just using the raw packet data from the JSON structure - this
is interesting for development and testing purposes for all library components).

```
usage: pfeiffersniff [-h] [-p PORT] [-s SIMFILE] [-d DEVICE] [-j LOGJSON]
                      [--showsim] [--noshowquery] [--noerror]

Simple access to Pfeiffer pumps on an RS485 bus attached to a serial port

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  Serial port to be used to access the RS485 bus
  -s SIMFILE, --simfile SIMFILE
                        Simulation file. One can supply a JSON dump that
                        should be injected instead of a real serial port
  -d DEVICE, --device DEVICE
                        Adds a device registerset to a given address
                        (ADR:DEVTYPE). Can be used multiple times
  -j LOGJSON, --logjson LOGJSON
                        Specifies a logfile that all captured packets are
                        appended to - in JSON format line per line
  --showsim             Show simulated messages
  --noshowquery         Disable output of query messages
  --noerror             Disable error messages (protocol violation, etc.)
```

For example to listen on ```/dev/ttyU1``` for messages, decoding messages
for a ```TC110``` on address 1 and a ```MVP015``` on address 2 recording
everything into a ```packets.json``` file:

```
pfeiffersniff -p /dev/ttyU1 -j ./packets.json -d 1:TC110 -d 2:MVP015
```

To replay the recorded packets afterwards without showing decoded query
messages and hiding protocol errors:

```
pfeiffersniff -s ./packets.json -d 1:TC110 -d 2:MVP015 --noshowquery --noerror
```
