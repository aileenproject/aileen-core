#!/bin/bash
#
# Script for configuring the software for the aileen server
# Using Ubuntu 18.04 LTS Desktop
#
# Helpful link we used for service composition:
# https://stackoverflow.com/questions/51025312/start-a-python-script-at-startup-automatically

# Info for hotspot
SSID=aileen
WPA_PASSWORD=Aileen-wifi
# Info for script location
AILEEN_SCRIPT_LOCATION=/home/aileen/Desktop/aileen

sudo apt-get update
sudo apt-get upgrade -y

# install openssh server
sudo apt-get install openssh-server

# install useful tools
sudo apt-get install vim -y
sudo apt install git -y
sudo apt install tree

# to get the hotspot working
sudo apt-get install dnsmasq
sudo nmcli device wifi hotspot con-name ${SSID} ssid ${SSID} band bg password ${WPA_PASSWORD}
# ensure it always starts
sudo nmcli con mod ${SSID} connection.autoconnect yes

# install aircrack
sudo apt install aircrack-ng -y

# install tmux
sudo apt-get install tmux -y

# ensure Python3 is working
alias python=python3
sudo apt install python3-pip
psudo() { sudo env PATH="$PATH" "$@"; } 

# install and configure postgresql
# sudo apt-get install postgresql postgresql-contrib -y
# TODO we're using sqlite for now

# install zsh because it's just nice
sudo apt install zsh
chsh -s $(which zsh)

# give aileen access to the tmp directory this is necessary for service
sudo chmod 755 /tmp/

# Create service scripts for aileen box
echo "#!/bin/bash
cd ${AILEEN_SCRIPT_LOCATION}/aileen
python3 manage.py run_box
" > ${AILEEN_SCRIPT_LOCATION}/start_aileen.sh

echo "#!/bin/bash
cd ${AILEEN_SCRIPT_LOCATION}/aileen
python3 manage.py stop_box
" > ${AILEEN_SCRIPT_LOCATION}/stop_aileen.sh


# create the aileen service
sudo echo "[Unit]
Description=Run aileen box

[Service]
Type=forking
User=aileen
ExecStart=/bin/bash -c '${AILEEN_SCRIPT_LOCATION}/start_aileen.sh'
ExecStop=/bin/bash -c '${AILEEN_SCRIPT_LOCATION}/stop_aileen.sh'
WorkingDirectory=/home/aileen

[Install]
WantedBy=multi-user.target" > /etc/systemd/system/aileen.service

chmod 775 ${AILEEN_SCRIPT_LOCATION}/start_aileen.sh
chmod 755 ${AILEEN_SCRIPT_LOCATION}/stop_aileen.sh

# TODO: Test this. It also is recommended not to call service scripts but to use direct commands
#       (see https://stackoverflow.com/a/46572318). If we use the Django location as WorkingDirectory,
#       we should be able to do that just fine and call manage.py directly.

# enable aileen box services
sudo systemctl daemon-reload
sudo systemctl enable aileen.service

# run aileen box
sudo service aileen start

# added stuff for launching programs at a key stroke
# sudo apt-get install xbindkeys -y


