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

 Import the thermoflex library and use discover() to find our product. 
 
```python
import thermoflex as tf

nodelist = tf.discover([115])
```

This will return a list of node-class objects containing data specific to that node device.
From here you will be able to assign all connected nodes to variables and call their methods(see Node Methods*hyperlink)

Next create muscle-class objects by calling


``` Python
muscle1 = tf.muscle(idnum = 0, resist= 300, diam= 2, length= 150)
muscle2 = tf.muscle(idnum = 1, resist= 290, diam= 2, length= 145)
```

Notice that the resistance, diameter, and length values are assigned in creating the class.

Next, assign the muscle objects to a node object by calling the setMuscle() command. This command takes the identification number and the muscle object as arguments

```Python
node0.setMuscle(0, muscle1)
node0.setMuscle(1, muscle2)
```

If you are using a session, this is where you want to create a session for your node. Do this by calling the *.session* method with the node being collected here:

```Python
session0 = tf.session(node0)
```

From here, you can add commands to your command buffer. The commands are as follows.

| Node Command                         | Function                                                                                                                                  |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| status()                             | Checks the status of the node and prints its status to the terminal                                                                       |
| reset()                              | Resets at the node level, can be extrapolated to reset the entire network                                                                 |
| setLogmode(mode)                     | Sets the logging mode of the node                                                                                                         |
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

| Muscle Command                   | Function                                                                                                                                  |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| changeMusclemos(*mosfetnum*:int) | Manually changes the mosfet number of the selected muscle. The mosfet number is set automatically when the muscle is assigned to a node;  |
| setMode(conmode)                 | Sets the data type that a given muscle receives for its setSetpoint() command; conmode : (percent, volts, amps, ohms, train)              |
| setSetpoint(setpoint:float)      | Sets the setpoint of the muscle at the node.                                                                                              |
| setEnable(bool)                  | Sets the enable status of the muscle in the node.                                                                                         |

