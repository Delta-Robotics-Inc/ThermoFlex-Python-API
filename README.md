# Thermoflex Python API


### System Requirements

- [Python 3.12 or greater](https://www.python.org/)
- [Pyserial 3.5 or greater](https://pyserial.readthedocs.io/en/latest/pyserial.html)

### Introduction

The Thermoflex muscle is a current activated artificial muscle that is designed to have a low profile and simple activation and deactivation sequence. The purpose of this library is provide a universal python API for communicating with and directing ThermoFlex Node devices over USB and `pyserial`.


# Download and Installation


To install our software, the most common method is through pip:

```bash
pip install thermoflex
```

You can install manually by downloading the files from our Github release page and installing the package with pip.

[Github Releases Page](https://github.com/Delta-Robotics-Inc/ThermoFlex-Python-API/releases)

### For Developers
You can also install manually by cloning this repository and running the following commands. This is good if you want to contribute to the library or work with an older/prototype version.,
```bash
git clone https://github.com/Delta-Robotics-Inc/ThermoFlex-Python-API
cd ThermoFlex-Python-API
pip install .\python-serial\               # Use for normal installation (not for development)
pip install --editable .\python-serial\    # OR Install for developement (changes made to repository source code reflects in your `thermoflex` package
```


# Launch and Use

 Import the thermoflex library and use .discover() to find your Node Controller. 
 
The `tf.discover()` method searches for USB devices with the Node Controller signature, creating a "NodeNet" object for each one found. A NodeNet represents a network of one or more Node Controllers, where additional devices can be connected via CAN bus to the primary USB-connected node. This allows you to control an entire network of nodes through a single USB connection.

For most users working with a single node, you can simply access the first node in the network:

```python
import thermoflex as tf
network = tf.discover()[0] # Find all Node networks over USB and connects to the first one found (0th index)
node0 = network.node_list[0]  # Access the first node in the network
```

For advanced users working with multiple nodes, you have several options:
- Access specific nodes by their position in the network's node list
- Identify nodes by testing messages to determine which node responds
- Each node has a permanent unique ID number accessible using `node.id`. You can identify the Node that you want this way after seeing it respond.

Additionally, each NodeNet provides two special Node objects:
- `network.self_node`: Direct access to the node connected via USB
- `network.broadcast_node`: Send commands to all nodes in the network simultaneously

Once you have your connected node bound, you can call its status, reset and logging commands. To use the muscles, you need to create [Muscle](#muscle-commands) objects.


To create [Muscle](#muscle-commands)-class objects, start by calling tf.muscle(). This is where you need input your `portNum` that you want the muscle to connect to (0=M1 and 1=M2 when looking at the phyisical Node Controller port labels)


``` Python
muscle1 = tf.Muscle(portNum=0, masternode=node0)
muscle2 = tf.Muscle(portNum=1) # You can make an orphaned muscle
```

All Muscle objects need to be attached to a Node to operate correctly. This can be done at initialization (like muscle1 above) or by using one of the following methods:
```Python
node0.attachMuscle(muscle2, 1)
# OR
muscle2.attach(node0, 1)
```

From here, you can send the Node and Muscles commands.

**Command Formats:**
- [Node Commands](#node-commands)
- [Muscle Commands](#muscle-commands)

These commands should be in the format:
```Python
muscle1.enable()  # Muscle command

node0.enable(muscle1)  # Node command version (does the same thing)
```

Note that for all `Muscle` commands, there exists a similar method in the `Node` object

### Sessions (experimental)

Our built-in session logging system can create a filesystem that exports to a higher level folder. Sessions track the incoming and outgoing serial data and saves it to a `.ses`, storing Node network and send/received packet information. This data can be analyzed by the `SessionAnalyzer` class. **Note: This feature is experimental. Feel free to create your own logging logic in your scripts.**

```Python
sessionl = tf.Session.sessionl
session1 = session[0]
```

### Developer install instructions

for testing purposes, use the command
```
pip install -e $SRC
```
with $SRC being the path to the [python-serial](python-serial/) folder. This will install the files as a test library.

## Program Commands

| **Program Commands**  | **Function**                                                            |
| --------------------- | ----------------------------------------------------------------------- |
| discover(*prodid*)    | finds connected nodes from the product id (*prodid*)                    |
| update()              | updates all of the networks                                             |
| updatenet(*network*)  | updates the *network*                                                   |
| delay(*time*)         | continuously calls update on all of the networks until *time* is called |
| endsession(*session*) | Ends and deletes the *session*                                          |
| endAll()              | Ends and deletes all sessions, nodes, and networks                      |

[Program Glossary](/docs/Thermoflex%20Glossary.md#program)

## NodeNet Commands

| **NodeNet Commands** | **Function**                                                                            |
| -------------------- | --------------------------------------------------------------------------------------- |
| refreshDevices()     | updates the status for all devices on a NodeNet                                         |
| addNode(*nodeid*)    | creates a new Node with the given *nodeid*                                              |
| removeNode(*nodeid*) | removes a Node object with *nodeid* from the given NodeNet's internal node list         |
| getDevice(*nodeid*)  | gets the Node object with *nodeid* and attaches it to the NodeNet                       |
| openPort()           | Opens the port associated with the network, Started upon initialization                 |
| closePort()          | Closes the port associated with the network                                             |
| start_serial()       | starts the serial loop for sending and receiving commands. started upon initialization. |

[NodeNet Glossary](/docs/Thermoflex%20Glossary.md#nodenet)

## Node Commands

| **Node Commands**                    | **Function**                                                                                                                          |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| status()                             | Checks the status of the node and returns its status                                                                                      |
| getStatus()                          | Returns the latest node status received                                                                                                   |
| reset()                              | Resets at the node level, can be extrapolated to reset the entire network                                                                 |
| setLogmode(mode)                     | Sets the logging mode of the node; mode:(0:'none', 1:'compact', 2:'dump', 3:'readable dump')                                              |
| setMode(conmode, device)             | Sets the input mode of the node; conmode : (percent, volts, amps, ohms, train); device : (all,node,m1,m2,...,m*n*)                        |
| setSetpoint(musc, conmode, setpoint) | Sets the point at which the node actuates to; musc: *muscle id number*; conmode : (percent, volts, amps, ohms, train); setpoint : *float* |
| setMuscle(portNum,muscle)              | Assigns a muscle to the node; will have presets in the future                                                                             |
| enable(muscle)                       | Enables the selected muscle to act on the value set by setSetpoint(); enable : (*muscle object*)                                          |
| enableAll                            | Enables all connected muscles of the node                                                                                                 |
| disable(muscle)                      | Disables the selected muscle : (m1,m2,...,m*n*)                                                                                           |
| disableAll                           | Disables all connected muscles of the node                                                                                                |
| update                               | Sends and receives the packets to "update" the node state                                                                                 |

[Node Glossary](/docs/Thermoflex%20Glossary.md#node)

## Muscle Commands

| **Muscle Command**                   | **Function**                                                                                                                          |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| changeMusclemos(*mosfetnum*:int) | Manually changes the mosfet number of the selected muscle. The mosfet number is set automatically when the muscle is assigned to a node;  |
| setMode(conmode)                 | Sets the data type that a given muscle receives for its setSetpoint() command; conmode : (percent, volts, amps, ohms, train)              |
| setSetpoint(setpoint:float)      | Sets the setpoint of the muscle at the node.                                                                                              |
| setEnable(bool)                  | Sets the enable status of the muscle in the node.                                                                                         |

[Muscle](/docs/Thermoflex%20Glossary.md#muscle)
