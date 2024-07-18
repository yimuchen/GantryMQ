# Setting up a dummy server for software interaction testing

For software testing, we have provided a [`conda`][conda] environment file in
this repository such that users can test the software capabilities of the
server before fully deploying. We chose `conda` over a providing docker, as
this allows for more flexible deployment when modifying the source code files,
as allowing the modules to access the underlying hardware when required.

```bash
# Cloning the repository
git clone https://github.com/UMDCMS/GantryMQ
# Getting external dependencies
bash GantryMQ/external/fetch_external.sh

# Creating the base conda environment and loading the virtual environment
conda env create --file GantryMQ/environment_server.yml
conda activate gantry_mq_server

# Compiling the required C++ code
cd GantryMQ/ && 
CXX=$(which g++) LD_LIBRARY_PATH=${CONDA_PREFIX}/lib cmake ./ && cmake --build ./
cd ../
```

This should be enough to compile everything required. At this point, you will
be able to host a server using the commands given in the main
[README.md](../README.md), though certain hardware will likely not work. In
this case, you might want to set up a dummy version of the hardware interfaces
for testing.

[conda]: https://conda.io/projects/conda/en/latest/index.html
