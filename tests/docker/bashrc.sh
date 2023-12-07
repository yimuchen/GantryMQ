# Custom bashrc script to be used for docker session initialization

# Running the build script everytime on launch to check for updates
CXX=/usr/bin/g++ cmake ./
CXX=/usr/bin/g++ cmake --build ./

# Setting up python path
export PYTHONPATH=$PYTHONPATH:/srv/src/gmqserver/
