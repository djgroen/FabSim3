# 
# Copyright (C) University College London, 2007-2014, all rights reserved.
# 
# This file is part of FabSim and is CONFIDENTIAL. You may not work 
# with, install, use, duplicate, modify, redistribute or share this
# file, or any part thereof, other than as allowed by any agreement
# specifically made by you with University College London.
# 
# no batch system


cd /home/hamid/Downloads/FabSim3_refactor/localhost_exe/FabSim3/results/validation_localhost_4/RUNS/ssudan_ccamp
/bin/true || true

# copy files from config folder
config_dir=/home/hamid/Downloads/FabSim3_refactor/localhost_exe/FabSim3/config_files/validation
rsync -pthrvz --exclude SWEEP $config_dir/* .

# copy files from SWEEP folder
rsync -pthrvz $config_dir/SWEEP/ssudan_ccamp/ .
export PYTHONPATH=/home/hamid/Downloads/FabSim3_M27/flee_master:$PYTHONPATH

/usr/bin/env > env.log

mpirun -np 4 python3 run_par.py input_csv source_data 0 simsetting.csv > out.csv

run_UNHCR_uncertainty="False"
if [[ "${run_UNHCR_uncertainty,,}" == "true" ]]
then
	mpirun -np 4 python3 run_UNHCR_uncertainty.py input_csv source_data 0 simsetting.csv > out_uncertainty.csv
fi