#!/usr/bin/env python
#
# Copyright (c) 2025, Juniper Networks Inc.
#
# Script to emulate Cisco/Arista's show interface status layout

from jnpr.junos import Device
from lxml import etree
from os import getenv
import re

# We only support ethernet interfaces, but the interface filter can be changed here
ALLOWED_INTERFACE_TYPES = ( 'fe', 'ge', 'xe', 'mge', 'et', 'ae' )

# Get connection info out of the environment for debugging.  Otherwise assume an on-box script
JUNOS_HOST = getenv("JUNOS_HOST")
JUNOS_USERNAME = getenv("JUNOS_USERNAME")
JUNOS_PASSWORD = getenv("JUNOS_PASSWORD")

# Normalize XML for output
device_params = {"normalize": True}

# Require all 3 env variables to be set to try to make a remote call
if JUNOS_HOST is not None and JUNOS_USERNAME is not None and JUNOS_PASSWORD is not None:
    device_params['host'] = JUNOS_HOST
    device_params['user'] = JUNOS_USERNAME
    device_params['passwd'] = JUNOS_PASSWORD

def main():
    with Device(**device_params) as jdev:

        # Fetch all interface information - This can take a while on older platforms so the RPC timeout is extended
        rsp = jdev.rpc.get_interface_information(extensive=True, dev_timeout=180)
        # Fetch the inventory for later reference
        hwrsp = jdev.rpc.get_chassis_inventory()
        # We need another RPC call to get the VLAN data
        switchrsp = jdev.rpc.get_ethernet_switching_interface_details()

        # NOTE: Fetching the full ethernet switching interface XML for the entire switch saves at least 25% 
        # execution time vs making an interface scoped API call for just that interface's data, assuming most 
        # interfaces are in switching mode.

        # Print the header immediately after completing RPC calls but before parsing
        print('{:<14}{:<10}{:<10}{:<7}{:<8}{:<12}{:<20}{:<16}'.format("Int","Status","Mode","VLAN","Duplex","Speed","Media","Description"))

        for interface in rsp.findall('physical-interface'):
            interface_info = {}
            interface_name = interface.find('name').text

            # Filter out non-ethernet interfaces
            if not interface_name.startswith(ALLOWED_INTERFACE_TYPES):
                continue

            interface_info['name'] = interface_name

            # If we're auto-negotiate, try to pull the interface speed out of the auto-neg data first, then fall back to interface speed
            interface_speed = interface.find('speed').text
            auto_negotiate = interface.find('if-auto-negotiation')
            if auto_negotiate is not None:
                if auto_negotiate.text == "disabled":
                   interface_info['speed'] = interface_speed
                else:
                    link_speed = interface.xpath('./ethernet-autonegotiation/local-info/local-link-speed')
                    if len(link_speed) > 0:
                        interface_info['speed'] = link_speed[0].text
                    else:
                        # Normalize some speeds where Junos spits them out in differing formats
                        interface_info['speed'] = interface_speed.replace("0mbps","0 Mbps").replace("0Gbps","0 Gbps")
            elif interface_speed == "Unspecified":
                interface_info['speed'] = ''
            else:
                interface_info['speed'] = interface_speed.replace("0mbps","0 Mbps").replace("0Gbps","0 Gbps")

            link_mode = interface.find('link-mode')
            if link_mode is not None:
                # Strip off "-duplex" for character limit reasons
                interface_info['duplex'] = re.sub("-duplex","", link_mode.text, flags=re.IGNORECASE)
            else:
                # If link-mode is not set, fall back to Duplex
                duplex = interface.find('duplex')
                if duplex is not None:
                    interface_info['duplex'] = re.sub("-duplex","", duplex.text, flags=re.IGNORECASE)
                else:
                    interface_info['duplex'] = ""
            
            # Extract the FPC/PIC/PORT numbers for future use
            intre = re.compile(r'\D+(\d+)\/(\d+)\/(\d+)\:?(\d+)?')
            intres = intre.match(interface_name)

            # If we were able to match a standard Junos physical interface, try to find a transceiver
            if intres is not None:
                #print(etree.tostring(hwrsp, encoding="UTF-8", pretty_print=True).decode('utf-8'))

                xpath = "./chassis/chassis-module[name = 'FPC "+intres.group(1)+"']/chassis-sub-module[name = 'PIC "+intres.group(2)+"']/chassis-sub-sub-module[name = 'Xcvr "+intres.group(3)+"']"
                for module in hwrsp.xpath(xpath):
                    xcvr_desc = module.find('description')

                    if xcvr_desc is not None:
                        interface_info['media'] = xcvr_desc.text
             
            # If we don't have a media type, grab it from the physical interface 
            if not 'media' in interface_info:
                # Fall back to just using the interfaces listed media type, if any
                media_type = interface.find('if-media-type')
                if media_type is not None:
                    interface_info['media'] = media_type.text
                else:
                    interface_info['media'] = ''

            # Use Cisco style admin/oper state notation
            interface_info['status'] = interface.find('admin-status').text + "/" + interface.find('oper-status').text

            # Description may not show up in the XML output
            description = interface.find('description')

            if description is not None:
                interface_info['description'] = description.text
            else:
                interface_info['description'] = ""

            # Everything else could fail to match, so seed VLAN info with an empty string
            interface_info['vlan'] = ''
            interface_info['interface_mode'] = ''

            # Get logical interface for unit 0 and 32767 (SP LAG detection) only
            unit0_name = interface_info['name'] + ".0"
            unit32767_name = interface_info['name'] + ".32767"
            for logical_interface in interface.findall('logical-interface'):
                name = logical_interface.find('name')
                if name is not None and ( name.text == unit0_name or name.text == unit32767_name):
                    #print(etree.tostring(logical_interface, encoding="UTF-8", pretty_print=True).decode('utf-8'))
                    # We found a unit 0, grab its address family
                    address_family_name = logical_interface.xpath('./address-family/address-family-name')

                    if address_family_name and (address_family_name[0].text == 'inet' or address_family_name[0].text == 'inet6'):
                        # Just for grins, make note of a routed unit 0
                        interface_info['interface_mode'] = "routed"

                    elif address_family_name and address_family_name[0].text == 'aenet':
                        # Detect a LAG member and reflect its parent
                        ae_bundle = logical_interface.xpath('./address-family/ae-bundle-name')
                        if len(ae_bundle) > 0 and ae_bundle[0].text.startswith('ae'):
                            interface_info['interface_mode'] = "in " + ae_bundle[0].text.split('.')[0]

                    elif address_family_name and address_family_name[0].text == 'eth-switch':
                        # Get the address family trunk flag
                        port_mode = logical_interface.xpath('./address-family/address-family-flags/ifff-port-mode-trunk')
                        if(len(port_mode) > 0):
                            interface_info['interface_mode'] = 'trunk'
                        else:
                            interface_info['interface_mode'] = 'access'

                        xpath = ("./l2ng-l2ald-iff-interface-entry/l2ng-l2ald-iff-interface-entry[l2iff-interface-name = '"+unit0_name+"']/../l2ng-l2ald-iff-interface-entry")
                        for vlan in switchrsp.xpath(xpath):
                            if vlan is None:
                                continue

                            tagness = vlan.find('l2iff-interface-vlan-member-tagness')

                            if(tagness is not None and tagness.text == "untagged"):
                                vlan_id = vlan.find('l2iff-interface-vlan-id')
                                if vlan_id is not None:
                                    interface_info['vlan'] = vlan_id.text

                    # We only want a single unit.  If we hit a unit 0, don't grab unit 32767
                    break

            # Print each interface as we fetch it so large/older switches don't appear to be blocking indefinitely
            print('{:<14}{:<10}{:<10}{:<7}{:<8}{:<12}{:<20}{:<16}'.format(interface_info['name'],interface_info['status'],interface_info['interface_mode'],interface_info['vlan'],interface_info['duplex'],interface_info['speed'],interface_info['media'],interface_info['description']))


if __name__ == '__main__':
    main()