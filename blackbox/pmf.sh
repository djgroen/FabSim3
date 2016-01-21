#!/bin/sh
# 
# This source file is part of the FabSim software toolkit, which is distributed under the BSD 3-Clause license. 
# Please refer to LICENSE for detailed information regarding the licensing.
#
# Legacy implementation of the Potentials of Mean Force calculation routines.

in=$4 #../python
out=$5 #../python
ibi_script_dir=$7
ref_dir=$6
i=$3
atom1=$1
atom2=$2
lammps_data=lammps_data_file
#lammps_data=CG_first_interaction.lammps05
echo $1, $2, $3, $4, $5, $6, $7
python $ibi_script_dir/PMF.py lammps_input_file $in/in.CG.lammps wham_correct_file $ref_dir/wham_output_AA  out_directory $out number $i wham_executable_path /home/james/bin//wham CG_in_file in.CG.lammps.1  atom_type1 $atom1 atom_type2 $atom2 potential_base $in/pot.5.new.   > ./pmf.out 

