#!/usr/bin/env python
#
# Copyright (c) 2025, Juniper Networks Inc.
#
# Script to output Unicast/Broadcast/Multicast packet counters for all physical interfaces

from jnpr.junos import Device
from lxml import etree
from os import getenv
import re

# We only support physical ethernet interfaces, but the interface filter can be changed here
ALLOWED_INTERFACE_TYPES = ( 'fe', 'ge', 'xe', 'mge', 'et' )

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
        # We need another RPC call to get the VLAN data
        switchrsp = jdev.rpc.get_ethernet_switching_interface_details()

        # Print the header immediately after completing RPC calls but before parsing
        print('{:<18}{:<6}{:<18}{:<18}{:<18}{:<18}{:<18}{:<18}'.format("Interface","AE","Unicast RX","Unicast TX","Broadcast RX","Broadcast TX","Multicast RX","Multicast TX"))

        for interface in rsp.findall('physical-interface'):
            interface_stats = {}
            interface_name = interface.find('name').text

            # Filter out non-ethernet interfaces
            if not interface_name.startswith(ALLOWED_INTERFACE_TYPES):
                continue

            interface_stats = {}

            interface_stats['name'] = interface_name

            eth_stats = interface.find('ethernet-mac-statistics')

            # Easier to just build a dict of the whole statistics subtree
            for stat in eth_stats:
                interface_stats[stat.tag] = stat.text

            # Get logical interface for unit 0 and 32767 (SP LAG detection) only
            unit0_name = interface_stats['name'] + ".0"
            unit32767_name = interface_stats['name'] + ".32767"
            for logical_interface in interface.findall('logical-interface'):
                name = logical_interface.find('name')
                if name is not None and ( name.text == unit0_name or name.text == unit32767_name):
                    #print(etree.tostring(logical_interface, encoding="UTF-8", pretty_print=True).decode('utf-8'))
                    # We found a unit 0, grab its address family
                    address_family_name = logical_interface.xpath('./address-family/address-family-name')

                    if address_family_name and address_family_name[0].text == 'aenet':
                        # Detect a LAG member and reflect its parent
                        ae_bundle = logical_interface.xpath('./address-family/ae-bundle-name')
                        if len(ae_bundle) > 0 and ae_bundle[0].text.startswith('ae'):
                            interface_stats['ae'] = ae_bundle[0].text.split('.')[0]

                    # We only want a single unit.  If we hit a unit 0, don't grab unit 32767
                    break

            #print(interface_stats)
            if not 'ae' in interface_stats.keys():
                interface_stats['ae'] = ''

            # Print each interface as we fetch it so large/older switches don't appear to be blocking indefinitely
            print('{:<18}{:<6}{:<18}{:<18}{:<18}{:<18}{:<18}{:<18}'.format(interface_stats['name'],interface_stats['ae'],interface_stats['input-unicasts'],interface_stats['output-unicasts'],interface_stats['input-broadcasts'],interface_stats['output-broadcasts'],interface_stats['input-multicasts'],interface_stats['output-multicasts']))

if __name__ == '__main__':
    main()