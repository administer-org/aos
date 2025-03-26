# pyxfluff 2025

echo "
# Welcome to the AOS installer!

! Please note at the moment only Linux-based platforms are supported. Windows/macOS can be used to serve, but this utility will only install for Linux.

This tool will fully install and set up an Administer AOS instance. It will also install a systemd unit. Please note that root permissions are required for setting up the systemd unit.
"

{
    echo "Checking for Python..."
    python3 --version
    python3 -m pip -V
} || {
    echo "[x] Python or pip is not installed. Please install it from your package manager and try again."
    exit 1
}

echo "Now we'll start by having you edit your configuration with nano. You will need a MongoDB instance ready. Press enter to continue."
read 

cp config.json.templ config.json
nano config.json

echo -n "
Would you like to edit the AOS environment file (__aos__.json)? This is where you edit the port and host that AOS will serve on. 

Please note that modifying [state] will harm AOS's functionality. We have prefilled [workers] for your current server so there is no need to touch it either.

[y]es/[n]o): 
"
read edit_env

THREADS="\"workers\": $(nproc --all)"
sed -i "s|\"workers\": 8|$THREADS|g" __aos__.json

if [[ "$edit_env" == "y" || "$edit_env" == "yes" ]]; then
    nano __aos__.json
fi


echo "< Initializing environment"

python3 -m pip install uv
python3 -m uv venv

sudo mkdir /etc/adm
sudo touch /etc/adm/log

source .venv/bin/activate

uv pip install .

echo "< Installing systemd unit"

WD="$(pwd)"
ES="$(pwd)/.venv/bin/python3 -m AOS serve"

sudo cp AOS/installer/example_unit.service /etc/systemd/system/adm.service
sudo sed -i "s|\$WD|$WD|g" /etc/systemd/system/adm.service
sudo sed -i "s|\$ES|$ES|g" /etc/systemd/system/adm.service

sudo systemctl daemon-reload
sudo systemctl enable adm
sudo systemctl start adm

echo "
All done! Administer is now running at whatever URL you defined in your __aos__.json file.

The service was installed to /etc/systemd/system/aos.service incase you need to modify it.
"

tail -f /etc/adm/log
