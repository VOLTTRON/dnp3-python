
## To demonstrate master outstation communication at different VMs:
1. Create two [Linux system](https://www.linux.org/pages/download/) virtual machines (VMs) with different IP addresses, then install the dnp3-python library on both VMs (We can use virtualization software such as [VirtualBox](https://www.virtualbox.org/) or [VMware](https://www.vmware.com/) to create the VMs.)
- After creating two VMs, use the command line to confirm the IP address of each VM:
	```shell
	ip addr show
	```
	- VM1 [*IP: 192.168.14.165*]: 
		```shell
		nino@nino-vm:~$ ip addr show
		1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
		    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
		    inet 127.0.0.1/8 scope host lo
		       valid_lft forever preferred_lft forever
		    inet6 ::1/128 scope host 
		       valid_lft forever preferred_lft forever
		2: ens33: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
		    link/ether 00:0c:29:ca:3a:e4 brd ff:ff:ff:ff:ff:ff
		    altname enp2s1
		    inet 192.168.14.165/24 brd 192.168.14.255 scope global dynamic noprefixroute ens33
		       valid_lft 1697sec preferred_lft 1697sec
		    inet6 fe80::db21:86ae:a9de:5d4e/64 scope link noprefixroute 
		       valid_lft forever preferred_lft forever
		```
	- VM2 [*IP: 192.168.14.167*]:
		```shell
		nino@nino-vm:~$ ip addr show
		1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
		    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
		    inet 127.0.0.1/8 scope host lo
		       valid_lft forever preferred_lft forever
		    inet6 ::1/128 scope host 
		       valid_lft forever preferred_lft forever
		2: ens33: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
		    link/ether 00:50:56:31:73:4c brd ff:ff:ff:ff:ff:ff
		    altname enp2s1
		    inet 192.168.14.167/24 brd 192.168.14.255 scope global dynamic noprefixroute ens33
		       valid_lft 1702sec preferred_lft 1702sec
		    inet6 fe80::2f65:e8c7:a44d:b72b/64 scope link noprefixroute 
		       valid_lft forever preferred_lft forever
		```
- Use the command to install the [dnp3-python](https://pypi.org/project/dnp3-python/) package on each VM:
	```shell
	pip install dnp3-python
	```
2.	Set one of the VMs to act as the master. Here's a simple example script that sends a request to link the outstation:
	```shell
	dnp3demo master --outstation-ip= 192.168.14.167
	```
3.	Set the other VM to act as the outstation. Here's a simple example script that sends a request to link the master:
	```shell
	dnp3demo outstation
	```
4.	Verify that the communication is working by checking the output of the master, It should print the following contents:
- Master:
	```shell
	ms(1680886137163) INFO    tcpclient - Connecting to: 192.168.14.167
	ms(1680886137167) INFO    tcpclient - Connected to: 192.168.14.167
	channel state change: OPEN
	==== Master Operation MENU ==================================
	<ao> - set analog-output point value (for remote control)
	<bo> - set binary-output point value (for remote control)
	<dd> - display/polling (outstation) database
	<dc> - display configuration
	=================================================================
	
	======== Your Input Here: ==(master)======
	```
- Outstation:
	```shell
	ms(1680886137121) INFO    server - Accepted connection from: 192.168.14.165
	==== Outstation Operation MENU ==================================
	<ai> - update analog-input point value (for local reading)
	<ao> - update analog-output point value (for local control)
	<bi> - update binary-input point value (for local reading)
	<bo> - update binary-output point value (for local control)
	<dd> - display database
	<dc> - display configuration
	=================================================================

	======== Your Input Here: ==(outstation)======
	```

This is just a simple example to demonstrate the basic communication between a master and an outstation. We can modify the agents to send and receive more complex data and handle other types of requests.

