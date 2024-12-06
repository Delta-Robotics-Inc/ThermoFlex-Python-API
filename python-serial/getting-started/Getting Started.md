*Important Dependencies*
    pyserial-3.5 or greater
    python-3.12 or greater

First steps

    Ensure that you have a Node and Muscle device. 
    
    Install the thermoflex library. You can do this 3 different ways.
        1. type this command into Powershell or command
        ```bash
        pip install thermoflex
        ```
        2. From the thermoflex repository, download the python-serial folder,cd to the build folder, and type this command.
        
        ```bash
        pip install thermoflex-0.0.3.tar.gz 
        ```
        
        3. After downloading the thermoflex repository, cd into the folder and type this command
        ```bash
        pip install python-serial/
        ```
    After installing the library, connect the Muscle to the Node and the Node to the computer. 

    There is an example python script muscle-simple.py in the getting started folder to help you understand the flow of the system.
    Simply run the file and the muscle should contract, update for 5 seconds, and then release. Then the program will end.

    The README in the thermoflex repository has a glossary containing all of the working commands in the repository.
