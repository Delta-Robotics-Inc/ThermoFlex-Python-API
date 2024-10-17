from setuptools import setup

 
Description = "Thermoflex repository"
Describe_long = "This is the repository for the thermoflex muscle by Delta Robotics"
    
 
setup(
      name="thermoflex",
      version="0.0.1",
      install_requires=['pyserial','importlib-serial','importlib-serial.tools.list_ports', 'importlib-time', 'importlib-threading'],
      description=Description,
      package_dir={"":"tf-src"},
      long_description=Describe_long,
      
      )
    

