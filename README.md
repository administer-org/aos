<div align = "center">
<img src="https://github.com/administer-org/administer/raw/main/.readme/Administer-Text.png?raw=true" width="512">

# AOS

[![administer-org - aos](https://img.shields.io/static/v1?label=administer-org&message=aos&color=green&logo=github)](https://github.com/administer-org/aos "Go to GitHub repo") [![stars - AOS](https://img.shields.io/github/stars/administer-org/aos?style=social)](https://github.com/administer-org/aos) [![forks - AOS](https://img.shields.io/github/forks/administer-org/aos?style=social)](https://github.com/administer-org/aos)

[![GitHub tag](https://img.shields.io/github/tag/administer-org/aos?include_prereleases=&sort=semver&color=green)](https://github.com/administer-org/aos/releases/) [![License](https://img.shields.io/badge/License-AGPL--3.0-green)](#license) [![issues - AOS](https://img.shields.io/github/issues/administer-org/aos)](https://github.com/administer-org/aos/issues) [![Hits-of-Code](https://hitsofcode.com/github/administer-org/aos?branch=main)](https://hitsofcode.com/github/administer-org/aos/view?branch=main)

</div>

# What is it?

The Administer AOS is a FastAPI program which manages Administer applications, collects statistics, and completes recurring tasks. It is designed for [Administer 2.0 and later](https://github.com/administer-org/administer) panels.

For everything knowledge related (recommended specs, installation, API reference, ...) please refer to our official documentation.

https://docs.admsoftware.org/AOS/information/about

# Installation & configuration

Please refer to our Quickstart Guide on the official documentation.

https://docs.admsoftware.org/AOS/maintaining/setup

Once you have installed AOS, log into the webpanel to set it up. It runs at :8020 by default, so you can visit the Admin Interface at MACHINE_IP:8020/a/.

## Demo

We do not have a live demo yet, but when we do you will be able to use it at https://demo.admsoftware.org. 

## Development installation

Run the following (assuming you already have python3 and pip):

```sh
pip install uv

uv venv

# Enter the venv.. it varies from OS to OS so if this doesn't work just run the command it tells you to
source .venv/bin/activate

uv pip install .
```

# Privacy Policy

See here: https://docs.admsoftware.org/legal/privacy

# Contributions

We welcome contributions as long as they are meaningful. Please ensure you are familiar with our code standards and libraries before making pull requests. For larger changes, you may want to [discuss a change in our Discord beforehand.](https://to.admsoftware.org/discord)

# License

All projects operated by Administer Software and your usage of it is governed under the GNU AGPL 3.0 license.

Administer Software 2024-2025
