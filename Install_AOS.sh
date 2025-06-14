# pyxfluff 2025

echo "
# Welcome to the AOS installer!

! Please note at the moment only Linux-based platforms are supported. Windows/macOS can be used to serve, but this utility will only install for Linux.
    > If you are on Windows or macOS, you can install manually (read the commands inside of Install_AOS.sh) or run \`pip install AOS\` for a complete installation.

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

echo "Now we'll start by having you edit your configuration with GNU nano. You will need a MongoDB instance ready. Press enter to continue."
read 

cp config.json.templ ._config.json
nano ._config.json

echo -n "
Would you like to edit the AOS environment file (._aos.json)? This is where you edit the port and host that AOS will serve on. By default, AOS serves on 0.0.0.0:8200, which can also be changed by using the CLI (\`aos core serve HOST PORT\`).
You can also change plugins which are auto-loaded in this file.

Modifying [state] can break AOS and reporting features. We have prefilled [workers] for your current server so there is no need to touch it either.

[y]es/[n]o): 
"
read edit_env

THREADS="\"workers\": $(nproc --all)"
sed -i "s|\"workers\": 8|$THREADS|g" ._aos.json

if [[ "$edit_env" == "y" || "$edit_env" == "yes" ]]; then
    nano ._aos.json
fi

echo "< Initializing environment"

python3 -m pip install uv --break-system-packages
python3 -m uv venv

sudo mkdir /etc/adm
sudo touch /etc/adm/log
sudo chmod 7777 /etc/adm /etc/adm/log

source .venv/bin/activate

echo "< Installing AOS packages"

uv pip install .

echo "< Installing systemd unit"

WD="$(pwd)"
ES="$(pwd)/.venv/bin/python3 -m AOS core serve"

sudo cp AOS/installer/example_unit.service /etc/systemd/system/adm.service
sudo sed -i "s|\$WD|$WD|g" /etc/systemd/system/adm.service
sudo sed -i "s|\$ES|$ES|g" /etc/systemd/system/adm.service

echo "< Reloading systemd config"

sudo systemctl daemon-reload
sudo systemctl enable adm
sudo systemctl start adm

echo "All done! AOS is now running at the URL defined in your ._aos.json file.

The service was installed to /etc/systemd/system/adm.service incase you need to modify it.
"

tail -f /etc/adm/log
