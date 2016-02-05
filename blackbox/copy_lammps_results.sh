#!/bin/sh
# 
# This source file is part of the FabSim software toolkit, which is distributed under the BSD 3-Clause license. 
# Please refer to LICENSE for detailed information regarding the licensing.
#
# Simple bash scripts to copy relevant LAMMPS output to a working directory.

out_dir=$1
work_dir=$2
i=$3

cp $out_dir/in.CG.lammps $work_dir/in.CG.lammps.$i
cp $out_dir/new_CG.prod$i.log $work_dir/
cp $out_dir/tmp.$i.rdf $work_dir/

