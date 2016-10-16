#!/bin/bash
echo > '/var/lib/dhcp/dhcpd.leases'
echo "1" > /proc/sys/net/ipv4/ip_forward
service isc-dhcp-server restart

ifconfig at0 up
ifconfig at0 192.168.3.1 netmask 255.255.255.0
ifconfig at0 mtu 1400

iptables --flush
iptables --table nat --flush
iptables --delete-chain
iptables --table nat --delete-chain


route add -net 192.168.3.0 netmask 255.255.255.0 gw 192.168.3.1

iptables -P FORWARD ACCEPT
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

dhcpd -cf /etc/dhcp/dhcpd.conf at0
