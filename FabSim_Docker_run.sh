#!/bin/bash

docker run --rm -v $PWD:/FabSim3  -e USER=$USER  -e USERID=$UID --hostname VECMA -ti fabsim
