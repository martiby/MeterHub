# MeterHub

The application captures all meters of the building installation, and makes them available via an HTTP JSON API. 
The different devices (meters, solar inverters, wallboxes, ...) with their different interfaces (USB, RS485, ...) 
are available for different applications via a common interface. 
Applications based on this are e.g.: Visualisation and databases, solar-controlled wallboxes, battery storage, ... 
The application is written in Python and usually runs on a Raspberry Pi. The specific configuration is defined directly in meterhub.py.

## Example:

  http://home:8008/

    {
      "time": "2022-01-23 00:08:38", 
      "grid_imp_eto": 3985744,
      "grid_exp_eto": 18804181, 
      "grid_p": 513, 
      "pv1_eto": 16152530, 
      "pv1_p": 0, 
      "car_eto": 735688, 
      "car_p": 0,  
      "car_amp": 6, 
      "car_phase": 1,  
      "car_state": "complete", 
      "water_vto": 1130154, 
      ...
    }

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