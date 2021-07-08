gcc TrafficGenerator.c -o TrafficGenerator
mn
sudo tcpdump -i any icmp & ./TrafficGenerator
