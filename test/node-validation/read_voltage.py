import argparse
import csv
import os
import time
import thermoflex as tf


def sample_voltage(nodes, duration=10.0, interval=0.1, out_file="./voltage_readings.csv"):
    start = time.time()
    with open(out_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        print("Writing to file: ", os.path.abspath(out_file))
        writer.writerow(["timestamp", "node_id", "supply_voltage"])
        csvfile.flush()  # Ensure header is written immediately
        
        while time.time() - start < duration:
            for node in nodes:
                try:
                    node.status("compact")
                    v = node.node_status.get("volt_supply")
                    nid = ".".join(str(b) for b in node.id)
                    
                    # Validate data before writing
                    if v is not None and nid:
                        writer.writerow([time.time(), nid, v])
                        csvfile.flush()  # Flush after each write to ensure data is saved
                        print(f"Node {nid} supply voltage: {v:.2f}V")
                    else:
                        print(f"Warning: Invalid data for node {nid}: voltage={v}")
                        
                except Exception as e:
                    print(f"Error reading from node: {e}")
                    
            time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description='Log node supply voltage over time')
    parser.add_argument('--duration', type=float, default=10.0, help='logging duration in seconds')
    parser.add_argument('--interval', type=float, default=0.1, help='sample interval in seconds')
    parser.add_argument('--outfile', default='./voltage_readings.csv', help='CSV output file')
    args = parser.parse_args()

    print("Begin Supply Voltage Validation")

    nets = tf.discover([105])
    for net in nets:
        net.refreshDevices()

    node_list = [node for net in nets for node in net.node_list]
    sample_voltage(node_list, args.duration, args.interval, args.outfile)
    tf.endAll()


if __name__ == '__main__':
    main()
