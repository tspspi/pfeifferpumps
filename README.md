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
