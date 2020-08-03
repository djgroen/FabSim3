# 
# Copyright (C) University College London, 2007-2014, all rights reserved.
# 
# This file is part of FabSim and is CONFIDENTIAL. You may not work 
# with, install, use, duplicate, modify, redistribute or share this
# file, or any part thereof, other than as allowed by any agreement
# specifically made by you with University College London.
# 
# no batch system


# FabDummy Exec Template: 
cd /home/wouter/VECMA/FabSim3/localhost_exe/FabSim3/results/dummy_test_localhost_16
/bin/true || true

/usr/bin/env > env.log
echo "Starting dummy job, which will print the contents of dummy.txt."
/bin/cat dummy.txt
