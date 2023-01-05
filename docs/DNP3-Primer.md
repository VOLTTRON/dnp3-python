# DNP3 Primer

Distributed Network Protocol (DNP or DNP3) has achieved a large-scale acceptance since its introduction in 1993. This
protocol is an immediately deployable solution for monitoring remote sites because it was developed for communication of
critical infrastructure status, allowing for reliable remote control.

GE-Harris Canada (formerly Westronic, Inc.) is generally credited with the seminal work on the protocol. This protocol
is, however, currently implemented by an extensive range of manufacturers in a variety of industrial applications, such
as electric utilities.

DNP3 is composed of three layers of the OSI seven-layer functions model. These layers are application layer, data link
layer, and transport layer. Also, DNP3 can be transmitted over a serial bus connection or over a TCP/IP network.

## Main DNP3 Capabilities

As an intelligent and robust SCADA protocol, DNP3 gives you many capabilities. Some of them are:

- DNP3 can request and respond with multiple data types in single messages
- Response without request (unsolicited messages)
- It allows multiple masters and peer-to-peer operations
- It supports time synchronization and a standard time format
- It includes only changed data in response messages

## DNP3 uses a Master/Remote Model

DNP3 is typically used between centrally located masters and distributed remotes. The master provides the interface
between the human network manager and the monitoring system. The remote (RTUs and intelligent electronic devices)
provides the interface between the master and the physical device(s) being monitored and/or controlled.
![Master/Remote Model](https://user-images.githubusercontent.com/28743873/209717298-eab58d7b-bbc9-40b9-b631-fac2596a9d44.png)
The master and remote both use a library of common objects to exchange information. The DNP3 protocol contains carefully
designed capabilities. These capabilities enable it to be used reliably even over media that may be subject to noisy
interference.

The DNP3 protocol is a polled protocol. When the master station connects to a remote, an integrity poll is performed.
Integrity polls are important for DNP3 addressing. This is because they return all buffered values for a data point and
include the current value of the point as well.

## The DNP3 Protocol Specification is Based An Object Model

DNP3 is based on an object model. This model reduces the bit mapping of data that is traditionally required by other
less object-oriented protocols. It also reduces the wide disparity of status monitoring and control paradigms generally
found in protocols that provide virtually no pre-defined objects.

Purists of these alternate protocols would insist that any required object can be 'built' from existing objects. Having
some pre-defined objects though makes DNP3 a somewhat more comfortable design and deployment framework for SCADA
engineers and technicians.

**DNP3 Data Object Library**

DNP3 protocol contains data points with a variety of data types. Data pointsare grouped according to their data types,
and the groups are called dataobjects. Examples of data objects are, binary input object, binary outputobject, analog
input object, counter object, freeze counter object, string object,and analog output object. The collection of these
data object groups is referredto as the data object library.

DNP3 data objects can be further defined through object variants, such as the16-bit analog input, 32-bit floating-point
analog input, and binary input, all ofwhich contain time.

****DNP3 Groups and Variations****

*Point Types*

There are several important point types

- binary input
- analog input
- counter input
- binary (status) output
- analog (status) output

which we can see some are inputs and some are outputs, but it is important to recognize that your view of whether
something is an*input*or*output*depends on your frame of reference. Our frame is that of the DNP3 master. In general, we
read from inputs and we write to outputs.

- Indices*

For each of the point types, DNP3 supports multiple instances. These instances are identified by a zero-based index. In
some contexts, this is called the point number.

*Group*

Groups tell you something about the characteristics of the point type at the specified index. That is, binary input at
index 2 might report itself in multiple ways, for example a current or frozen value. It could also be descriptive of the
value - for example the number of binary outputs or the maximum binary output index. So, the group gives a semantic
meaning to the data.

*Variation*

Another consideration is the variation. Variations tell you about the encoding of the value. In general, you can think
of this as being the data type (e.g. a 16-bit integer), but DNP3 supports a more diverse set of encodings than what
software developers are normally familiar with. The particular set of variations depends on the group, so you don’t have
freedom to choose them arbitrarily - you need to select the correct pairing.

### More on Layering

Communication circuits between the devices are often imperfect. They are susceptible to noise and signal distortion.
DNP3 software is layered to provide reliable data transmission and to effect an organized approach to the transmission
of data and commands.
![Master/Remote Model](https://user-images.githubusercontent.com/28743873/209717325-ffbcc480-134b-4036-a903-b90e6795e063.png)
Link Layer Responsibility
The link layer has the responsibility of making the physical link reliable. It does this by providing error detection
and duplicate frame detection. The link layer sends and receives packets, which in DNP3 terminology, are called frames.
Sometimes transmission of more than one frame is necessary to transport all of the information from one device to
another.

A DNP3 frame consists of a header and data section. The header specifies the frame size, contains data link control
information and identifies the DNP3 source and destination device addresses. The data section is commonly called the
payload and contains data passed down from the layers above.

Transport Layer
The transport layer has the responsibility of breaking long application layer messages into smaller packets sized for
the link layer to transmit, and, when receiving, to reassemble frames into longer application layer messages. In DNP3
the transport layer is incorporated into the application layer. The transport layer requires only a single octet
overhead to do its job.
Therefore, since the link layer can handle only 250 data octets, and one of those is used for the transport function,
each link layer frame can hold as many as 249 application layer octets.

More about communication details, see

- [DNP3 Tutorial Part 4: Understanding DNP3 Message Structure](https://www.dpstele.com/dnp3/tutorial-understanding-message-structure.php)
- [DNP3 Tutorial Part 5: Understanding DNP3 Packet Layers](https://www.dpstele.com/dnp3/understanding-traversing-troubleshooting-layered-communication.php)

## Case study—**Reading**

Now that we can understand the jargon, let's talk about reading from the device. Suppose we want to get the current (
also know as*static*) value of a binary input at index 2. How do we specify that for DNP3?

There is no direct way to specify “binary input”. Instead, it is inferred by the group. The simplest way we can do this
is group 1, variation 1. The group selects binary inputs and the variation selects only the binary value.

If we want read an analog inputs encoded as 32-bit signed integers, then that is group 30 and variation 1. An analog
input encoded as double precision is again group 30, but this time variation 6.

A description of valid combinations of group and variation of the DNP3
specification can be found
in [data object specification](https://www.vtscada.com/help/Content/D_Tags/Dev_DNPObjTypes.htm).  [OpenDNP3](https://github.com/automatak/dnp3)
package has a partial list, but it is not complete.

## Summary

It should be apparent by now that DNP3 is a protocol that fits well into the data acquisition world. It transports data
as generic values, it has a rich set of functions, and it was designed to work in a wide area communications network.
The standardized approach of groups and variations, and link, transport and application layers, plus public availability
makes DNP3 a protocol to be regarded.

### Useful references

- [A DNP3 Protocol Primer](https://www.dnp.org/Portals/0/AboutUs/DNP3%20Primer%20Rev%20A.pdf)
- [DNP3 Tutorial](https://www.dpstele.com/dnp3/index.php)
- [data object specification](https://www.vtscada.com/help/Content/D_Tags/Dev_DNPObjTypes.htm)