# 
# Copyright (C) University College London, 2007-2014, all rights reserved.
# 
# This file is part of FabSim and is CONFIDENTIAL. You may not work 
# with, install, use, duplicate, modify, redistribute or share this
# file, or any part thereof, other than as allowed by any agreement
# specifically made by you with University College London.
# 
# no batch system


cd /home/hamid/Downloads/FabSim3_refactor/localhost_exe/FabSim3/results/mali_localhost_16_vvp_LoR_PCESampler_po2/RUNS/run_3
/bin/true || true

# copy files from config folder
config_dir=/home/hamid/Downloads/FabSim3_refactor/localhost_exe/FabSim3/config_files/mali_vvp_LoR_PCESampler_po2
rsync -pthrvz --exclude SWEEP $config_dir/* .

# copy files from SWEEP folder
rsync -pthrvz $config_dir/SWEEP/run_3/ .

if [ -z "/home/hamid/Downloads/FabSim3_M27/flee_master" ]
then
	echo "Please set $flee_location in your deploy/machines_user.yml file."
else
	export PYTHONPATH=/home/hamid/Downloads/FabSim3_M27/flee_master:$PYTHONPATH
fi

/usr/bin/env > env.log

python3 run.py input_csv source_data 10 simsetting.csv > out.csv

run_UNHCR_uncertainty="False"
if [[ "${run_UNHCR_uncertainty,,}" == "true" ]]
then
	python3 run_UNHCR_uncertainty.py input_csv source_data 10 simsetting.csv > out_uncertainty.csv
fi