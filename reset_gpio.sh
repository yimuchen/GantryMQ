#!/bin/bash

for gpio in $(ls -d /sys/class/gpio/gpio?? ); do
  local pin=$(basename $gpio) ;
  echo ${pin/gpio} > /sys/class/gpio/unexport;
done ;
