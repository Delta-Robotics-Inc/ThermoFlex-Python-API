
# Glossary

## Program

| **Program Commands**  | **Function**                                                            |
| --------------------- | ----------------------------------------------------------------------- |
| discover(*prodid*)    | finds connected nodes from the product id (*prodid*)                    |
| update()              | updates all of the networks                                             |
| updatenet(*network*)  | updates the *network*                                                   |
| delay(*time*)         | continuously calls update on all of the networks until *time* is called |
| endsession(*session*) | Ends and deletes the *session*                                          |
| endAll()              | Ends and deletes all sessions, nodes, and networks                      |

## NodeNet

| **NodeNet Commands** | **Function**                                                                            |
| -------------------- | --------------------------------------------------------------------------------------- |
| refreshDevices()     | updates the status for all devices on a NodeNet                                         |
| addNode(*nodeid*)    | creates a new Node with the given *nodeid*                                              |
| removeNode(*nodeid*) | removes a Node object with *nodeid* from the given NodeNet's internal node list         |
| getDevice(*nodeid*)  | gets the Node object with *nodeid* and attaches it to the NodeNet                       |
| openPort()           | Opens the port associated with the network, Started upon initialization                 |
| closePort()          | Closes the port associated with the network                                             |
| start_serial()       | starts the serial loop for sending and receiving commands. started upon initialization. |

| **NodeNet Attributes** | **Purpose**                                                                                                               |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| .idnum                 | the index number of the connected NodeNet in the global list of NodeNet objects                                           |
| .port                  | name of the serial port assigned to the NodeNet                                                                           |
| .arduino               | the serial port object for sending and receiving data                                                                     |
| .broadcast_node        | a virtual node that 'broadcasts' the message received to all connected Node's                                             |
| .self_node             | the Node that is the 'self' on the NodeNet. Messages sent to this Node are not distributed and execute within the device. |
| .node_list             | a list of Nodes connected to the NodeNet                                                                                  |
| .command_buff          | the command buffer for sending commands to the NodeNet for distribution                                                   |
| .sess                  | the Session object associated with the node                                                                               |
| .debug_name            | the NodeNet's debug name; used for debugging purposes                                                                     |

## Node

| **Node Commands**                    | **Function**                                                                                                                              |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| status()                             | Checks the status of the node and returns its status                                                                                      |
| getStatus()                          | Returns the latest node status received                                                                                                   |
| reset()                              | Resets at the node level, can be extrapolated to reset the entire network                                                                 |
| setLogmode(mode)                     | Sets the logging mode of the node; mode:(0:'none', 1:'compact', 2:'dump', 3:'readable dump')                                              |
| setMode(conmode, device)             | Sets the input mode of the node; conmode : (percent, volts, amps, ohms, train); device : (all,node,m1,m2,...,m*n*)                        |
| setSetpoint(musc, conmode, setpoint) | Sets the point at which the node actuates to; musc: *muscle id number*; conmode : (percent, volts, amps, ohms, train); setpoint : *float* |
| attachMuscle(portNum,muscle)              | Assigns a muscle to the node; will have presets in the future                                                                             |
| enable(muscle)                       | Enables the selected muscle to act on the value set by setSetpoint(); enable : (*muscle object*)                                          |
| enableAll()                          | Enables all connected muscles of the node                                                                                                 |
| disable(muscle)                      | Disables the selected muscle : (m1,m2,...,m*n*)                                                                                           |
| disableAll()                         | Disables all connected muscles of the node                                                                                                |
| update()                             | Sends and receives the packets to "update" the node state                                                                                 |

| **Node Attributes** | **Purpose**                                                                    |
| ------------------- | ------------------------------------------------------------------------------ |
| .index              | the index of the node in the global nodelist                                   |
| .serial             | the serial port name. None by default                                          |
| .net                | the connected network                                                          |
| .arduino            | the serial port information and address                                        |
| .logmode            | integer logmode for internal use                                               |
| .id                 | the id number of the connected node                                            |
| .canid              | the id specific to the Can bus of the connected node;seperate from the node id |
| .firmware           | the firmware number of the connected node                                      |
| .board_version      | the board version of the connected node                                        |
| .node_status        | the dictionary of the most recent statuses of the connected node               |
| .mosports           | the number of connected mosports                                               |
| .muscles            | dictionary of the connected muscles                                            |
| .logstate           | dictionary containing the current log types and status                         |
| .status_curr        | current string status of the node.                                             |
| .latest_response    | latest response from the node.                                                 |
| .bufflist           | buffer list for commands                                                       |
| .lastcmd            | the last command sent                                                          |

## Muscle

| **Muscle Command**                   | **Function**                                                                                                                                  |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| changeMusclemos(*mosfetnum*:int) | Manually changes the mosfet number of the selected muscle. The mosfet number is set automatically when the muscle is assigned to a node;  |
| setMode(conmode)                 | Sets the data type that a given muscle receives for its setSetpoint() command; conmode : (percent, volts, amps, ohms, train)              |
| setSetpoint(setpoint:float)      | Sets the setpoint of the muscle at the node.                                                                                              |
| setEnable(bool)                  | Sets the enable status of the muscle in the node.                                                                                         |

| **Muscle Attributes** | Purpose                                                    |
| --------------------- | ---------------------------------------------------------- |
| .portNum                | id number of the muscle connected to the node              |
| .mosfetnum            | number of the mosfet port that the muscle is connected to. |
| .resistance           | restance value of the muscle                               |
| .diameter             | diameter of the muscle                                     |
| .length               | travel length of the muscle                                |
| .cmode                | the current control mode of the muscle                     |
| .masternode           | the masternode of the muscle                               |
| .enable_status        | the enable status of the node                              |
| .train_state          | the train state of the muscle                              |
| .SMA_status           | the status of the muscle connected                         |
