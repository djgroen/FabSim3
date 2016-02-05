#!/bin/sh
# 
# This source file is part of the FabSim software toolkit, which is distributed under the BSD 3-Clause license. 
# Please refer to LICENSE for detailed information regarding the licensing.
#
# Script which converts output from data processing routines to input definitions for a new LAMMPS run.

work_dir=$1
config_dir=$2
config_name=$3
i=$4
ref_dir=$5

mkdir $config_dir/$config_name$i
cp $ref_dir/* $config_dir/$config_name$i/
#cp $ref_dir/CG_first_interaction.lammps05 $config_dir/$config_name$i/
cp $work_dir/in.CG.lammps.$i $config_dir/$config_name$i/in.CG.lammps 
cp $work_dir/pot.$i.new.* $config_dir/$config_name$i/ 
#cp $ref_dir/bond* $config_dir/$config_name$i/
