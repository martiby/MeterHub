# MeterHub

The application captures all meters of the building installation, and makes them available via an HTTP JSON API. 
The different devices (meters, solar inverters, wallboxes, ...) with their different interfaces (USB, RS485, ...) 
are available for different applications via a common interface. 
Applications based on this are e.g.: Visualisation and databases, solar-controlled wallboxes, battery storage, ... 
The application is written in Python and usually runs on a Raspberry Pi. The specific configuration is defined directly in meterhub.py.

# Supported devices:

* Solar inverters
    * Fronius Symo

* Electricity meter (RS485 Modbus)
    * Eastron SDM72
    * Eastron SDM120
    * Eastron SDM630
    
* Electricity meter (SML IR)
    * ISKRA MT175
    * ITRON 3.HZ
    * EMH eHZ

* Wallbox 
  * Go-e HomeFix
    
* Generic HTTP-API
  * ESP32 CAM (https://github.com/jomjol/AI-on-the-edge-device) 


# Install
**Python**
 
    pip3 install -r requirements.txt

**Install Service**  

    sudo cp meterhub.service /etc/systemd/system

# Use Service

**Commands** 

    sudo systemctl start meterhub
    sudo systemctl stop meterhub
    sudo systemctl restart meterhub
    sudo systemctl enable meterhub
    sudo systemctl disable meterhub

**Logging**

    sudo journalctl -u meterhub
    sudo journalctl -u meterhub -f