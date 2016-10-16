iptables --flush
iptables --table nat --flush
iptables --delete-chain
iptables --table nat --delete-chain

brctl addbr hacker
brctl addif hacker eth0
brctl addif hacker at0
ifconfig eth0 0.0.0.0 promisc up
ifconfig at0 0.0.0.0 promisc up

route add default gw 192.168.1.1

dhclient hacker
ifconfig hacker

echo 1 > /proc/sys/net/ipv4/ip_forward
