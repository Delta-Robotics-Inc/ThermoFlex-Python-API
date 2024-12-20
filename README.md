#### System Requirements

- Python 3.12 or greater
- Pyserial 3.5 or greater
## Introduction

###### The Thermoflex muscle is a current activated artificial muscle that is designed to have a low profile usage and simple activation and deactivation sequence. The purpose of this library is 2-fold; to become the working backend of the Delta hardware application and to allow for open-source development of the Nitinol muscle.

## Download and Installation


To install our software, you can use the pip and package methods

`pip install thermoflex`

or you can install manually by downloading the files from our Github and running the tfsetup.py file. Be sure that you are have the setuptools package installed if you choose to install manually.

( add Github site and link)

## Launch and Use

 Import the thermoflex library and use .discover() to find our product. 
 
```python
import thermoflex as tf

netlist = tf.discover()
network1 = netlist[0]
```

This will return a list of NodeNet-objects. Each NodeNet contains a list of Node-objects connected at initialization as well as a broadcast Node and a self Node device. From here you will be able to assign nodes to variables using the .getDevice() command.

``` Python
node0 = network1.node_list[0]
```

You can also assign the broadcast node and self node by calling a NodeNet's .broadcast_node and .self_node. 

``` Python
node_b = network1.broadcast_node
node_s = network1.self_node
```

Once you have your connected node bound, you can call its status, reset and logging commands. To use the muscles, you need to create Muscle objects
(see Node Methods*hyperlink)


To create Muscle-class objects, start by calling tf.muscle(). This is where you need input your *idnum*, *resistance*, *length*, and *diameter* values if you have them. 


``` Python
muscle1 = tf.muscle(idnum = 0, resist= 300, diam= 2, length= 150)
muscle2 = tf.muscle(idnum = 1, resist= 290, diam= 2, length= 145)
```

Note that the *idnum* field is the only field that is neccesary for creating the Muscle-object.

Next, assign the muscle objects to a node object by calling the .setMuscle() command. This command takes the identification number and the muscle object as arguments

```Python
node0.setMuscle(0, muscle1)
node0.setMuscle(1, muscle2)
```

Sessions are automatically created and create a filesystem that exports to a higher level folder. Sessions track the incoming and outgoing serial data and saves it to a .ses file and a .txt file. The .txt files are generated as plain messages, where as the .ses files have serialized messages. 

```Python
sessionl = tf.Session.sessionl
session1 = session[0]
```



| **Program Commands**  | **Function**                                                            |
| --------------------- | ----------------------------------------------------------------------- |
| discover(*prodid*)    | finds connected nodes from the product id (*prodid*)                    |
| update()              | updates all of the networks                                             |
| updatenet(*network*)  | updates the *network*                                                   |
| delay(*time*)         | continuously calls update on all of the networks until *time* is called |
| endsession(*session*) | Ends and deletes the *session*                                          |
| endAll()              | Ends and deletes all sessions, nodes, and networks                      |

| **NodeNet Commands** | **Function**                                                                            |
| -------------------- | --------------------------------------------------------------------------------------- |
| refreshDevices()     | updates the status for all devices on a NodeNet                                         |
| addNode(*nodeid*)    | creates a new Node with the given *nodeid*                                              |
| removeNode(*nodeid*) | removes a Node object with *nodeid* from the given NodeNet's internal node list         |
| getDevice(*nodeid*)  | gets the Node object with *nodeid* and attaches it to the NodeNet                       |
| openPort()           | Opens the port associated with the network, Started upon initialization                 |
| closePort()          | Closes the port associated with the network                                             |
| start_serial()       | starts the serial loop for sending and receiving commands. started upon initialization. |

From here, you can add commands to your command buffer. The commands are as follows.

| **Node Commands**                        | **Function**                                                                                                  |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| status()                             | Checks the status of the node and returns its status                                                                                      |
| getStatus()                          | Returns the latest node status received                                                                                                   |
| reset()                              | Resets at the node level, can be extrapolated to reset the entire network                                                                 |
| setLogmode(mode)                     | Sets the logging mode of the node; mode:(0:'none', 1:'compact', 2:'dump', 3:'readable dump')                                              |
| setMode(conmode, device)             | Sets the input mode of the node; conmode : (percent, volts, amps, ohms, train); device : (all,node,m1,m2,...,m*n*)                        |
| setSetpoint(musc, conmode, setpoint) | Sets the point at which the node actuates to; musc: *muscle id number*; conmode : (percent, volts, amps, ohms, train); setpoint : *float* |
| setMuscle(idnum,muscle)              | Assigns a muscle to the node; will have presets in the future                                                                             |
| enable(muscle)                       | Enables the selected muscle to act on the value set by setSetpoint(); enable : (*muscle object*)                                          |
| enableAll                            | Enables all connected muscles of the node                                                                                                 |
| disable(muscle)                      | Disables the selected muscle : (m1,m2,...,m*n*)                                                                                           |
| disableAll                           | Disables all connected muscles of the node                                                                                                |
| update                               | Sends and receives the packets to "update" the node state                                                                                 |
These commands should be in the format,

```Python
node0.enable(muscle1)
```

The muscle objects also have their own commands that are passed to their commanding node.  These commands are as follows.

| **Muscle Command**                   | **Function**                                                                                                                                  |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| changeMusclemos(*mosfetnum*:int) | Manually changes the mosfet number of the selected muscle. The mosfet number is set automatically when the muscle is assigned to a node;  |
| setMode(conmode)                 | Sets the data type that a given muscle receives for its setSetpoint() command; conmode : (percent, volts, amps, ohms, train)              |
| setSetpoint(setpoint:float)      | Sets the setpoint of the muscle at the node.                                                                                              |
| setEnable(bool)                  | Sets the enable status of the muscle in the node.                                                                                         |

Developer install instructions
for testing purposes, use the command
```
pip install -e $SRC
```
with $SRC being the path to the python-serial folder. This will install the files as a test library.