'''
Created on Tue Apr  2 18:53:24 2024

Code tested in Spyder Anaconda environment.

This program utilizes the resistance control mode with the ThermoFlex Python API.
Tested with thermoflex library v1.0.1 and Node Controller firmware v1.0.1

Summary
This script sets up a connection with a ThermoFlex Node Controller, logs data during a predefined experiment,
parses the data, and visualizes it in real-time using Matplotlib. The experiment is controlled via the ThermoFlex API,
and the data is continuously updated and displayed in a set of subplots.

@author: Mark Dannemiller
'''

import thermoflex as tf
import time
import matplotlib.pyplot as plt
from timeit import default_timer

# Data storage arrays
time_data = []
m1_en_data = []
vbatt_data = []
vld_data = []
amps_data = []
resist_data = []
pwm_data = []

def get_data(node, muscle):
    """Get and parse data from the node and muscle objects"""
    try:
        # Get node status
        node_status = node.getStatus()
        if node_status:
            # Parse node status data
            vbatt = node.node_status['volt_supply']
            if vbatt is not None:
                vbatt_data.append(vbatt)
                time_data.append(int(time.time() * 1000))  # Current time in ms

        # Get muscle status
        muscle_status = muscle.SMA_status
        if muscle_status:
            vld = muscle_status['load_voltdrop'][-1] if muscle_status['load_voltdrop'] else 0
            amps = muscle_status['load_amps'][-1] if muscle_status['load_amps'] else 0
            ohms = muscle_status['r_sns_ohms'][-1] if muscle_status['r_sns_ohms'] else 0
            pwm = muscle_status['pwm_out'][-1] if muscle_status['pwm_out'] else 0

            vld_data.append(vld)
            amps_data.append(amps)
            resist_data.append(ohms)
            pwm_data.append(pwm)
            m1_en_data.append(muscle.enable_status)

    except Exception as e:
        print(f"Error getting data: {e}")

def plot_data(ax, title, x_label, y_label, x_arr, y_arr, y_range, history):
    """Plot data with specified parameters"""
    ax.clear()
    start_index = len(x_arr) - history
    if start_index < 0 or history < 0:
        start_index = 0
        start_range = 0
    else:
        start_range = x_arr[start_index]
        
    for i in range(start_index, len(x_arr) - 1):
        if x_arr[i] < x_arr[i + 1]:
            # Normalize pwm_data to be between 0 and 1
            normalized_value = pwm_data[i] / 255.0
            # Get color from the 'cool' colormap
            color = plt.cm.cool(0.5)
            ax.plot(x_arr[i:i + 2], y_arr[i:i + 2], color)

    ax.set_xlim(start_range, x_arr[-1] + 1000)
    ax.set_ylim(0, y_range)
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)

def update_plot(history):
    """Update all plots with current data"""
    if len(time_data) > 0:
        plot_data(ax1, 'VBatt Data', 'Log Time (ms)', 'Voltage (V)', time_data, vbatt_data, 24, history)
        plot_data(ax2, 'V_LD Data', 'Log Time (ms)', 'Voltage (V)', time_data, vld_data, 30, history)
        plot_data(ax3, 'Amps Data', 'Log Time (ms)', 'Current (A)', time_data, amps_data, 100, history)
        plot_data(ax4, 'M2 Resist Data', 'Log Time (ms)', 'Resistance (mΩ)', time_data, resist_data, 1000, history)

        fig.tight_layout()
        plt.pause(0.001)

def delay(wait_time, node, muscle):
    """Delay while collecting data"""
    start = default_timer()
    while default_timer() - start < wait_time:
        get_data(node, muscle)
        tf.update()

# Initialize the plot
plt.style.use("fivethirtyeight")
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 8))

# Experiment parameters
wait1 = 300.0  # Main heating time
wait2 = 5.0    # Cooling time
setpoint = 170  # Resistance setpoint in mΩ (calibrated for 550°C)

# Discover and setup the ThermoFlex network
node_net = tf.discover([105])[0]  # Discover networks over USB and get the first one
node_net.refreshDevices()  # Discover all Node devices on the selected network
tf.delay(1)  # Wait for the devices to be discovered

node = node_net.node_list[0]  # Get the first connected Node
muscle = tf.Muscle(idnum=0)  # Create muscle object for M1
node.setMuscle(0, muscle)  # Assign the muscle to the Node at port 0

# Configure the muscle for resistance control
muscle.setMode("ohms")
muscle.setSetpoint(setpoint=setpoint)

# Start the experiment
node.disableAll()  # Ensure all muscles are disabled initially
tf.delay(0.5)  # Wait for commands to be processed

# Enable logging and start the muscle
node.setLogmode(2)  # Set to dump mode for detailed logging
muscle.setEnable(True)

# Run the main heating phase
delay(wait1, node, muscle)

# Disable the muscle and monitor cooling
node.disableAll()
delay(wait2, node, muscle)

# Print final data
print("Time data:", time_data)
print("Enable status:", m1_en_data)
print("Battery voltage:", vbatt_data)
print("Current:", amps_data)
print("Load voltage:", vld_data)
print("Resistance:", resist_data)
print("PWM:", pwm_data)

# Show final plot
update_plot(-1)

# Clean up
tf.endAll()
