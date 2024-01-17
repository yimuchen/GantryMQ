# Setting up a dummy server for software interaction testing

For software testing, we have provided a docker file in this repository such
that users can test the software capabilities of the server before fully
deploying, to build the image file, run the following command on your machine:

```bash
docker buildx build --file tests/docker/Dockerfile --tag gantrymq   \
       --network="host"  --platform ${PLATFORM}  --rm --load ./
```

The `${PLATFORM}` variable should match what machine you are running the test on
(tested using `linux/amd64`).

To start up the docker session run the command:

```bash
docker run -it                                              \
       --network="host"                                     \
       --platform ${PLATFORM}                               \
       --mount type=bind,source="${PWD}",target=/srv        \
       --privileged -v /dev/video1:/dev/video1              \
       gantrymq:latest                                      \
       /bin/bash --init-file "/srv/tests/docker/bashrc.sh"
```

Notice that if you are running in docker, it is likely that most of the hardware
will not function, and is not strictly a bug in the system. If you want to test
the camera device, modify the exposed device.
