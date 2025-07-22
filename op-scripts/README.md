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

A JunOS-ified version of the Cisco and Arista "show interface status" command for switches.

This script attempts to resolve the negotiatied link speed and state first.  If this is not available, it will fall back to the interface link speed.

If possible, inserted transceivers will be displayed. If it is not able to resolve a transceiver from inventory, it will fall back to the interface level media type (typically Copper or Fiber).
If a native VLAN is set on a trunk port, the native/untagged VLAN will be listed under the VLAN column

This script (mostly) only supports enterprise style configurations for VLAN resolution, where unit 0 is the sole unit on the port.
Service Provider style LACP interfaces will attempt to resolve the parent interface, but no VLAN tagging information will be available.
Pure layer 3 (family inet or inet6) interfaces will be displayed as routed, also with only unit 0 supported. 

#### Example Output 

``` 
dylanv@crsw1> op interface-status
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

### [ethernet-statistics.py](ethernet-statistics.py) 

An op script to display TX and RX packets for unicast, multicast and broadcast on a physical interface.

LACP interfaces will display the parent, but individual memeber statistics will be given.

The script does not attempt to separate switched or routed interfaces, and will display statistics for interfaces that are currently down.


#### Example Output 

``` 
mist@Theater-EX4100-F-12P> op ethernet-statistics 
Interface         AE    Unicast RX        Unicast TX        Broadcast RX      Broadcast TX      Multicast RX      Multicast TX      
ge-0/0/0                3957              10005             8261              181               243               11805             
ge-0/0/1                505435549         67829026          1234              10699841          74431             14750438          
ge-0/0/2                1601866           1120320           15032             22052145          4028241           15107533          
ge-0/0/3                19526894          80796704          252               22064925          122615            19011534          
ge-0/0/4                2094391602        1748661015        3444226           18961522          818007            18550263          
ge-0/0/5                23068066          24414945          585000            21823064          736687            18659651          
ge-0/0/6          ae0   0                 122               6                 1654              90327             137479            
ge-0/0/7          ae0   0                 20                5890              2717              90314             127115            
ge-0/0/8                2493111848        2404471822        304635            22244427          4864592           16077159          
ge-0/0/9                2370877733        2479524039        27                0                 10                2534603           
ge-0/0/10               320684580         854266677         2295157           20253489          2214112           18854252          
ge-0/0/11               14707536          11893610          71                22407456          162495            19371205          
mge-0/2/0               2598641736        2770416285        1358034           21190223          870130            20144768          
mge-0/2/1               0                 7020              0                 152958            0                 291562  
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