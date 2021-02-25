echo "Configuring iptables ..."
mkdir -p /etc/iptables/
# Base policies (drop all incoming, allow all outcoming, drop all forwarding)
sudo iptables -P INPUT ACCEPT
sudo iptables -P OUTPUT ACCEPT
sudo iptables -P FORWARD DROP
# Allow conntrack established connections
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
# Allow local loopback services
sudo iptables -A INPUT -i lo -j ACCEPT
# Allow ssh
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
# Allow http
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
# Allow https
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
# Allow dns
sudo iptables -A INPUT -p tcp --dport 53 -j ACCEPT
sudo iptables -A INPUT -p udp --dport 53 -j ACCEPT
# Allow watchdog
sudo iptables -A INPUT -p tcp --dport 3009 -j ACCEPT
# Allow monitor node exporter
sudo iptables -A INPUT -p tcp --dport 9100 -j ACCEPT
# Drop all the rest
sudo iptables -A INPUT -p tcp -j DROP
sudo iptables -A INPUT -p udp -j DROP
# Allow pings
sudo iptables -I INPUT -p icmp --icmp-type destination-unreachable -j ACCEPT
sudo iptables -I INPUT -p icmp --icmp-type source-quench -j ACCEPT
sudo iptables -I INPUT -p icmp --icmp-type time-exceeded -j ACCEPT
sudo bash -c 'iptables-save > /etc/iptables/rules.v4'
