import sys
import json
import thermoflex as tf

node_status, m1_status, m2_status, values = None, None, None, None

def get_node1_status():
    node_status = node1.status() # Get Status Dump
    print(node_status) # Make sure that this prints in a readable format
    """ Make output look like the following:
    <NodeID> Node Status {
        ...vars
    }
    """
    n1_muscle1_status = n1_muscle1.status() # Get Status Dump
    print(n1_muscle1_status)
    """
    <NodeID> Muscle 1 Status {
        ...vars
    }
    """
    n1_muscle2_status = n1_muscle2.status() # Get Status Dump
    print(n1_muscle2_status)
    """
    <NodeID> Muscle 2 Status {
        ...vars
    }
    """

# Repeat above method for node 2 status


if(__name__ == '__main__'):

    nodenet_list = tf.discover([105]) #input the product id and returns a list of nodes available
    nodenet = nodenet_list[0]

    # Get node 1 and node 2 from node net by id
    node1 = nodenet.getDevice([0x01, 0x02, 0x03])
    node2 = nodenet.getDevice([0x04, 0x05, 0x06])
    
    print(node1.status("dump")) # Print status dump
    print(node2.status("compact"))

    # Set up Node 1 and Muscles
    n1_muscle1 = tf.muscle(idnum=0, resist=340, diam=2, length=400)
    n1_muscle2 = tf.muscle(idnum=1, resist=340, diam=2, length=400)

    node1.setMuscle(0, n1_muscle1) # set muscle 1 to node 1 at id 0
    node1.setMuscle(1, n1_muscle2)

    # Set up Node 2 and Muscles
    n2_muscle1 = tf.muscle(idnum=0, resist=340, diam=2, length=400)
    n2_muscle2 = tf.muscle(idnum=1, resist=340, diam=2, length=400)

    node2.setMuscle(0, n2_muscle1) # set muscle 1 to node 2 at id 0
    node2.setMuscle(1, n2_muscle2)


    # Initialize muscle modes and setpoints beforehand
    n1_muscle1.setMode("ohms")
    n1_muscle1.setSetpoint(340)
    n1_muscle2.setMode("ohms")
    n1_muscle2.setSetpoint(340)

    n2_muscle1.setMode("ohms")
    n2_muscle1.setSetpoint(340)
    n2_muscle2.setMode("ohms")
    n2_muscle2.setSetpoint(340)

    # Communicate with Delta Client Javascript Application
    while True:
        try:
            input_data = json.dumps(input())  # Read data from stdin
            if(input() == 'get status'):
                print(f"Node Status: {node_status}\nMuscle 1 Status: {m1_status}\nMuscle 2 Status: {m2_status}")
            if(input() == 'node1 set-enable m1 true'):
                print(input_data)
                print(values)
                n1_muscle1.setEnable(True)
            elif(input() == 'node1 set-enable m1 false'):
                n1_muscle1.setEnable(False)
            elif(input() == 'node1 set-enable m2 true'):
                n1_muscle2.setEnable(True)
            elif(input() == 'node1 set-enable m2 false'):
                n1_muscle2.setEnable(False)
                # etc...
            
            elif(input() == "node1 status all"):
                get_node1_status()
            elif(input() == "node2 status all"):
                get_node2_status()
            else: 
                print(f"Python received input: {input_data}")  # Process the input and print the result
        except EOFError:
            break