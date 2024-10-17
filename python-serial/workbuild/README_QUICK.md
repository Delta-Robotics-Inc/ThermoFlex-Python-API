# Download and Installation


To install our software, you can use the pip and conda  package methods


`pip install thermoflex`

`conda install thermoflex`


or you can install manually by downloading the files from our Github and running the tf-setup.py file. 
Be sure that you are have the setuptools package installed 
 if you choose to install manually.

( add Github site and link)

# Launch and Use

 Import the thermoflex library and use discover() to find our product. 
```python
import thermoflex as tf


nodel = tf.discover([115])
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