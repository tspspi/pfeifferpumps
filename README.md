# Unofficial control library and CLI utility for Pfeiffer turbopumps

This is a simple _unofficial_ (it's in no way associated with Pfeiffer vaccuum
or any of their partners) Python library and utility collection to work with
Pfeiffer turbopumps via the RS485 interface.

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

* ```pfeiffercli``` is a simple command line utility that exposes core features
  of the libraries via the CLI to allow simple and easy monitoring of the bus
  and optionally controlling the attached pumps.

## Supported devices

| Type                 | Name  | Support / Comment            |
| -------------------- | ----- | ---------------------------- |
| Turbopump controller | TC110 | Protocol handler implemented |

## The protocol library

The protocol library is implemented in ```pfeifferproto.py```. It can simply be
imported using

```
from pfeifferproto import PfeifferProtocol, SerialProtocolViolation
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
