xxxxx

# Features

Devices:
* Abc
* CDE


# Install
**Python**
 
    pip3 install -r requirements.txt

**Install Service**  

    sudo cp meterhub.service /etc/systemd/system

#Service commands

Dienst: 

    sudo systemctl start meterhub
    sudo systemctl stop meterhub
    sudo systemctl restart meterhub
    sudo systemctl enable meterhub
    sudo systemctl disable meterhub

Logging:

    sudo journalctl -u meterhub
    sudo journalctl -u meterhub -f





