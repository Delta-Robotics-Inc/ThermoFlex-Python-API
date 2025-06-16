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
| refreshDevices()     | Updates the status for all devices on a NodeNet                                         |
| add_node(node_id)    | Creates a new Node with the given node_id or reactivates an existing inactive node      |
| remove_node(node_id) | Removes a Node from active nodes, optionally moving it to inactive nodes                |
| get_node(node_id)    | Gets the active Node object with node_id                                                |
| get_all_nodes()      | Returns a list of all active nodes in the network                                       |
| get_inactive_nodes() | Returns a list of all inactive/forgotten nodes in the network                           |
| openPort()           | Opens the port associated with the network (started upon initialization)                |
| closePort()          | Closes the port associated with the network                                             |
| start_serial()       | Starts the serial loop for sending and receiving commands (started upon initialization) |
| end_network()        | Cleans up all network resources and closes connections                                  |

| **NodeNet Attributes** | **Purpose**                                                                                                               |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| .idnum                 | The index number of the connected NodeNet in the global list of NodeNet objects                                           |
| .port                  | Name of the serial port assigned to the NodeNet                                                                           |
| .arduino               | The serial port object for sending and receiving data                                                                     |
| .broadcast_node        | A virtual node that 'broadcasts' messages to all connected nodes                                                          |
| .self_node             | The Node that is the 'self' on the NodeNet. Messages sent to this Node execute within the device                          |
| .active_nodes          | Dictionary of active nodes, keyed by node ID                                                                              |
| .inactive_nodes        | Dictionary of inactive/forgotten nodes, keyed by node ID                                                                  |
| .command_buff          | The command buffer for sending commands to the NodeNet for distribution                                                   |
| .sess                  | The Session object associated with the network                                                                            |
| .debug_name            | The NodeNet's debug name; used for debugging purposes                                                                     |

## Node

| **Node Commands**                    | **Function**                                                                                                                              |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| status(type)                         | Requests and collects status from the device; type: ('dump' or 'compact')                                                                 |
| getStatus()                          | Returns the latest node status received                                                                                                   |
| reset(device)                        | Sends reset command to the node or specified device                                                                                       |
| setLogmode(mode)                     | Sets the logging mode of the node; mode:(0:'none', 1:'compact', 2:'dump', 3:'readable dump')                                              |
| setMode(conmode, device)             | Sets the input mode of the node; conmode: (percent, volts, amps, ohms, train); device: (all, node, m1, m2, ..., m*n)                     |
| setSetpoint(setpoint, conmode, device)| Sets the actuation point; setpoint: float; conmode: (percent, volts, amps, ohms, train); device: (all, m1, m2, ..., m*n)                |
| attachMuscle(portNum, muscle)        | Assigns a muscle to the node at the specified port                                                                                        |
| enable(muscle)                       | Enables the selected muscle to act on the value set by setSetpoint()                                                                      |
| enableAll()                          | Enables all connected muscles of the node                                                                                                 |
| disable(muscle)                      | Disables the selected muscle                                                                                                              |
| disableAll()                         | Disables all connected muscles of the node                                                                                                |
| update_heartbeat(received)           | Updates heartbeat timestamps and status                                                                                                   |
| check_heartbeat_status()             | Checks if node has missed heartbeats and updates status                                                                                   |
| deactivate()                         | Marks node as inactive and disables all muscles                                                                                           |
| reactivate()                         | Reactivates a previously inactive node                                                                                                    |
| cleanup()                            | Cleans up node resources and disables all muscles                                                                                         |

| **Node Attributes** | **Purpose**                                                                    |
| ------------------- | ------------------------------------------------------------------------------ |
| .index              | The index of the node in the network                                           |
| .net                | The connected NodeNet instance                                                 |
| .arduino            | Reference to the network's serial port                                         |
| .logmode            | Integer logmode for internal use                                               |
| .id                 | The ID number of the node (list of integers)                                   |
| .canid              | The CAN bus ID of the node (separate from node ID)                             |
| .firmware           | The firmware version of the node                                               |
| .board_version      | The board version of the node                                                  |
| .node_status        | Dictionary of the most recent status values                                    |
| .mosports           | Number of available muscle ports                                               |
| .muscles            | Dictionary of connected muscles                                                |
| .logstate           | Dictionary containing current log types and status                             |
| .status_curr        | Current string status of the node                                              |
| .latest_resp        | Latest response from the node                                                  |
| .is_active          | Flag indicating if the node is currently active                                |
| .missed_heartbeats  | Counter for missed heartbeats                                                  |
| .heartbeat_timeout  | Timeout period for heartbeat monitoring                                        |

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
