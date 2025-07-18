# Junos Automation Scripts 

[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

The scripts in this folder are designed to be run directly on JunOS devices in operational mode.  

Note that the minimum tested version is JunOS 21.4R3-S5.

## Table of Contents

- [Contents](#contents)
- [Background](#background)
- [Install and Usage](#install-and-usage)
- [Maintainers](#maintainers)
- [Contributing](#contributing)
- [License](#license)

## Contents

### [interface-status.py](interface-status.py) 

A JunOS-ified version of the Cisco and Arista "show interface status command" for switches.

This script attempts to resolve the negotiatied link speed and state first.  If this is not available, it will fall back to the interface link speed.

If possible, inserted transceivers will be displayed. If it is not able to resolve a transceiver from inventory, it will fall back to the interface level media type (typically Copper or Fiber).
If a native VLAN is set on a trunk port, the native/untagged VLAN will be listed under the VLAN column

This script (mostly) only supports enterprise style configurations for VLAN resolution, where unit 0 is the sole unit on the port.
Service Provider style LACP interfaces will attempt to resolve the parent interface, but no VLAN tagging information will be available.
Pure layer 3 (family inet or inet6) interfaces will be displayed as routed, also with only unit 0 supported. 

#### Example Output 

``` 
dylanv@semaphore.com@crsw1.sea1.semaphore.net> op interface-status
Int           Status    Mode      VLAN   Duplex  Speed       Media               Description
ge-0/0/0      up/down   access    14     Full    1000 Mbps   SFP-LX10            Down fiber access port
ge-0/0/4      up/up     access    31     Full    1000 Mbps   SFP-LH              Up fiber access port
ge-0/0/33     up/up                      Full    1000 Mbps   SFP-LX10            Up fiber port - service provider
ge-1/0/2      up/up     access    1506   Full    1000 Mbps   SFP-SX              Up fiber access port
ge-4/0/5      up/up     in ae12          Full    1000 Mbps   Copper              Up copper LAG member
ge-4/0/6      up/up     in ae13          Full    1000 Mbps   Copper              Up copper LAG member
ge-4/0/18     up/down   trunk     2021   Full    Auto        Copper              Down copper trunk w/ native VLAN
et-4/1/2      up/up     in ae15          Full    40Gbps      QSFP+-40G-CU3M      Up fiber LAG member - service provider
et-4/1/3      up/up     in ae16          Full    40Gbps      QSFP+-40G-CU3M      Up fiber LAG member - service provider
ge-5/0/5      up/up     in ae12          Full    1000 Mbps   Copper              Up copper LAG member
ge-5/0/6      up/down   in ae13          Half    1000 Mbps   Copper              down copper LAG member
et-5/1/2      up/up     in ae15          Full    40Gbps      QSFP+-40G-CU3M      Up fiber LAG member - service provider
et-5/1/3      up/up     in ae16          Full    40Gbps      QSFP+-40G-CU3M      Up fiber LAG member - service provider
ae12          up/up     trunk                    2Gbps                           Up copper LACP bundle
ae13          up/up     trunk                    1Gbps                           Up copper LACP bundle
ae14          up/down   access    18                                             Down LACP bundle
ae15          up/up                              80 Gbps                         Up fiber LACP bundle - service provider
ae16          up/up                              80 Gbps                         Up fiber LACP bundle - service provider
```

## Install

Copy the script file to /var/db/scripts/op on your JunOS device.

Add the following configuration to the device:

```
set system scripts language python3
set system scripts op file <filename> [command <alias>]
```

The command alias is optional and the script can always be run directly via the filename.

## Usage

To execute an op script, run the following command from operational mode

```
op [script-name|command-alias] [arguments]
```

Not all scripts accept arguments.

## Remote Execution

All of the included op scripts can be run remotely via netconf over ssh, using the default port 830

To remotely execute the script, pass in the following environment variables

```
- JUNOS_HOST - Hostname or IP address of the dvice
- JUNOS_USERNAME - Local or remote username for RPC access
- JUNOS_PASSWORD - Password (pubkey auth not currently supported)
```

## Maintainers

[@dvanderhoof-juniper](https://github.com/dvanderhoof-juniper)

## Contributing

Feel free to [Open an issue](https://github.com/dvanderhoof-juniper/junos-automation/issues/new) or submit PRs.

## License

[MIT](LICENSE) © Juniper Networks