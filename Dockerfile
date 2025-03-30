# Use the Ubuntu Jammy base from Microsoft’s devcontainer images
FROM mcr.microsoft.com/devcontainers/base:jammy

# Install prerequisites and add the deadsnakes PPA for Python 3.11
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the default python3 to point to Python 3.11
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Optionally, upgrade pip
RUN python3 -m pip install --upgrade pip

# Create the dialout group if it doesn't exist and add the vscode user to it
RUN groupadd -f dialout && usermod -aG dialout vscode

# Set default shell to bash
SHELL ["/bin/bash", "-c"]
