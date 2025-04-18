
### System Requirements

- Python 3.12 or greater
- Pyserial 3.5 or greater

## Introduction

 The Thermoflex muscle is a current activated artificial muscle that is designed to have a low profile usage and simple activation and deactivation sequence. The purpose of this library is 2-fold; to become the working backend of the Delta hardware application and to allow for open-source development of the Nitinol muscle.

## First steps

Ensure that you have a Node and Muscle device. 

Install the thermoflex library. You can do this 3 different ways.
    
1. Type this command into Powershell
    
    ```
    pip install thermoflex
    ```
    
2. From the thermoflex repository, download the [python-serial](https://github.com/Delta-Robotics-Inc/ThermoFlex-Python-API/tree/main/python-serial) folder,cd to the build folder, and type this command.
    
    ```bash
    pip install python-serial/
    ``` 
    
3. Download the latest release from [Github Releases](https://github.com/Delta-Robotics-Inc/ThermoFlex-Python-API/releases), cd into the folder and type this command
    
     ```bash
    pip install thermoflex-1.0.2.tar.gz 
    ```
    *The version number is subject to change*

After installing the library, connect the Muscle to the Node and the Node to the computer. 

There is an example python script [muscle-simple.py](https://github.com/Delta-Robotics-Inc/ThermoFlex-Python-API/blob/main/getting-started/muscle-simple.py) in the getting started folder to help you understand the flow of the system.
Simply run the file and the muscle should contract, update for 5 seconds, and then release. Then the program will end.

There is a [Glossary](https://github.com/Delta-Robotics-Inc/ThermoFlex-Python-API/blob/main/docs/Thermoflex%20Glossary.md) of the working commands and features in the library.
