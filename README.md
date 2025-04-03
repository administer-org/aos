<div align = "center">
<img src="https://github.com/administer-org/administer/raw/main/.readme/Administer-Text.png?raw=true" width="512">

# App Server

[![administer-org - app-server](https://img.shields.io/static/v1?label=administer-org&message=app-server&color=green&logo=github)](https://github.com/administer-org/app-server "Go to GitHub repo") [![stars - app-server](https://img.shields.io/github/stars/administer-org/app-server?style=social)](https://github.com/administer-org/app-server) [![forks - app-server](https://img.shields.io/github/forks/administer-org/app-server?style=social)](https://github.com/administer-org/app-server)

[![GitHub tag](https://img.shields.io/github/tag/administer-org/app-server?include_prereleases=&sort=semver&color=green)](https://github.com/administer-org/app-server/releases/) [![License](https://img.shields.io/badge/License-AGPL--3.0-green)](#license) [![issues - app-server](https://img.shields.io/github/issues/administer-org/app-server)](https://github.com/administer-org/app-server/issues) [![Hits-of-Code](https://hitsofcode.com/github/administer-org/app-server?branch=main)](https://hitsofcode.com/github/administer-org/app-server/view?branch=main)

</div>


# What is it?

The App Server is a FastAPI/MongoDB program which stores apps for use in Administer and a website later on, there is no backend panel or anything. What you see is what you get.

## Installation Prerequisites

Install python3 3.13 and pip.

In addition to that, make sure you have a MongoDB instance which **runs locally ONLY** without a password. Because it will not have a password, exposing it to the internet is a bad idea.

# Installation

## Standard installation (recommended)

Just clone the repo and run the installer:
```sh
git clone https://github.com/administer-org/app-server

cd app-server

chmod +x Install_AOS.sh
./Install-AOS.sh
```

AOS and a systemd unit will be installed automatically.

## Development installation

Run the following (assuming you already have python3 and pip):
```sh
pip install uv

uv venv

# Enter the venv.. it varies from OS to OS so if this doesn't work just run the command it tells you to
source .venv/bin/activate

uv pip install .
```

And you're done! Make sure to edit your `__aos__.json` and `config.json` files, then run `aos`. 

## Privacy Policy

See here: https://docs.admsoftware.org/legal/privacy

## Contributions

We welcome contributions as long as they are meaningful. Please ensure you are familiar with our code standards and libraries before making pull requests. For larger changes, you may want to [discuss a change in our Discord beforehand.](https://administer.notpyx.me/to/discord)


## License

All of Administer and your usage of it is governed under the GNU AGPL 3.0 license.

<small>Administer Team 2024-2025-2025</small>
