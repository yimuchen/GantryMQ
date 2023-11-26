# Primary base image setup
FROM    ubuntu:23.10
WORKDIR /srv

# List of tools to install using standard apt-get
ARG MAKE_TOOLS="g++ libfmt-dev cmake"
ARG PYTHON_TOOLS="python3-dev python3-pybind11 pybind11-dev python3-pip python3-venv"
ARG DRS_TOOLS="libwxgtk3.2-dev libusb-dev libusb-1.0-0-dev"

# Installing common packages
RUN apt update ;                       \
    apt-get -y install ${MAKE_TOOLS} ${PYTHON_TOOLS} ${DRS_TOOLS}

## Installing python components (using pip to pin version if needed).
ENV  VIRTUAL_ENV=/opt/venv
ENV  PATH="$VIRTUAL_ENV/bin/:$PATH"
COPY ./tests/docker/requirements.txt ./requirements.txt
RUN  python3 -m venv --system-site-packages $VIRTUAL_ENV; \
     pip install -r requirements.txt
