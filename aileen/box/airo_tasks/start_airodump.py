#!/usr/bin/env python
# -*- coding: utf-8 -*-

from getpass import getuser
from typing import List

import click
import pexpect

from netifaces import interfaces as net_interfaces


def run_with_sudo(
    command: str, sudo_pwd: str, success_match: str, failure_matches: List[str]
):
    """This method uses pexpect to talk us through a sudo prompt before the actual command can be reached."""
    if sudo_pwd is None or sudo_pwd == "":
        print(
            'Warning: sudo password is empty, so running "%s" via sudo will probably not work.'
            % command
        )
    child = pexpect.spawn("sudo %s" % command, timeout=5)
    index = child.expect(["password for %s:" % getuser(), pexpect.TIMEOUT])
    if index > 0:
        print("Expected sudo password prompt, which did not appear it seems.")
        return
    child.sendline(sudo_pwd)
    index = child.expect(
        [success_match, *failure_matches, pexpect.EOF, pexpect.TIMEOUT], timeout=5
    )
    if index == 0:
        print(child.before, end=" ")
        child.interact()
    elif index <= len(failure_matches):
        print("Problem running command %s: %s" % (command, failure_matches[index - 1]))
    else:
        print("Problem running command %s: No reply" % command)


def find_interface(interfaces: List[str]) -> str:
    """Find out if one of the possible network interfaces is indeed present.
    Return the first one found or exit (with a message) if none can be found.
    We are trying to deal with a renaming that Airmon sometimes does (adding "mon")
    Attention: Airmon tends to completely rename interfaces, too, so it makes sense to check both
               original factory name and airmon-edited name. This is why the parameter is a list."""
    found_interface = None
    if not isinstance(interfaces, list):
        interfaces = str(interfaces).split(",")
    for interface in interfaces:
        if interface not in net_interfaces():
            # Try to see if the interface was already put into monitoring mode. Airmon renames it then.
            monitoring_interface = interface + "mon"
            if monitoring_interface in net_interfaces():
                print(
                    'interface %s does not exist, but with "mon" added it does.'
                    % interface
                )
                found_interface = monitoring_interface
        else:
            found_interface = interface
    if found_interface is None:
        print("Error: the interfaces you specified (%s) cannot be found" % interfaces)
        print("Available interfaces: %s" % net_interfaces())
        print("Maybe tweak the setting WIFI_INTERFACES ...")
        exit(2)
    return found_interface


def put_wifi_interface_in_monitor_mode(
    interface: str, path_to_airmon_ng: str, sudo_pwd: str
) -> str:
    """Run airmon-ng on this wifi interface. Airmon-ng usually changes the name, so we return the new one."""
    interfaces_before = net_interfaces()
    run_with_sudo(
        "%s start %s" % (path_to_airmon_ng, interface),
        sudo_pwd,
        "PHY",
        ["processes that could cause trouble"],
    )
    print(" monitor mode activated! ")
    interfaces_after = net_interfaces()
    # check if there is a difference in the two lists
    if set(interfaces_before) == set(interfaces_after):
        return interface
    else:
        return list(set(interfaces_after) - set(interfaces_before))[0]


def start_airodump(
    interface: str,
    path_to_airodump_ng: str,
    airodump_file_name_prefix: str,
    log_interval_in_seconds: int,
    sudo_pwd,
):
    """Start airodump, in a mode that writes csv each n seconds."""
    command = "%s %s -w %s --output-format csv --write-interval %d" % (
        path_to_airodump_ng,
        interface,
        airodump_file_name_prefix,
        log_interval_in_seconds,
    )
    run_with_sudo(command, sudo_pwd, "BSSID", ["No such device"])


@click.command()
@click.option("--sudo-pwd", type=str, help="Sudo password.")
@click.option(
    "--airmon-ng-path", type=str, help="Path to successfully launch airmon-ng."
)
@click.option("--airodump-path", type=str, help="Path to successfully launch airodump.")
@click.option(
    "--airodump-file-prefix", type=str, help="Path to the CSV file airodump writes to."
)
@click.option(
    "--wifi-interfaces",
    type=str,
    help="List of possible wifi interface names on this computer (comma-separated).",
)
@click.option(
    "--airodump-log-interval-in-seconds",
    type=int,
    help="Each n seconds, update the output CSV file.",
)
def start(
    sudo_pwd,
    airmon_ng_path,
    airodump_path,
    airodump_file_prefix,
    wifi_interfaces,
    airodump_log_interval_in_seconds,
):
    """Start airodump, be sure airomon monitors the right interface beforehand."""
    try:
        wifi_interface = find_interface(wifi_interfaces.split(","))
        wifi_interface = put_wifi_interface_in_monitor_mode(
            wifi_interface, airmon_ng_path, sudo_pwd
        )
        start_airodump(
            wifi_interface,
            airodump_path,
            airodump_file_prefix,
            airodump_log_interval_in_seconds,
            sudo_pwd,
        )
    except KeyboardInterrupt:
        print("KeyboardInterrupt!")
        exit(1)
    except Exception as e:
        print("Problem: %s" % e)
        exit(2)


# To test
# python start_airodump.py --wifi-interfaces wlan1 --airmon-ng-path airmon-ng --airodump-path airodump-ng --airodump-file-prefix testing_shit --airodump-log-interval-in-seconds 5 --sudo-pwd <PassWord>


if __name__ == "__main__":
    start()
