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
cd /home/hamid/Downloads/FabSim3_refactor/localhost_exe/FabSim3/results/dummy_test_localhost_16/RUNS/d2_5
/bin/true || true

# copy files from config folder
config_dir=/home/hamid/Downloads/FabSim3_refactor/localhost_exe/FabSim3/config_files/dummy_test
rsync -pthrvz --exclude SWEEP $config_dir/* .

# copy files from SWEEP folder
rsync -pthrvz $config_dir/SWEEP/d2/ .

/usr/bin/env > env.log
echo "Starting dummy job, which will print the contents of dummy.txt."
/bin/cat dummy.txt
