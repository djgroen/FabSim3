#!/bin/sh

in=$4 #../python
atom=$1 #../python
out=$5 #../python
ibi_script_dir=../python
i=$2
pres=$3

python $ibi_script_dir/IBI.py lammps_input_file $in/in.CG.lammps lammps_output_file $out/in.CG.lammps LAMMPS_data_file $atom/CG_first_interaction.lammps05 lammps_rdf_file $in/tmp.$i.rdf correct_rdf_base $atom/rdf potential_base $in/pot.$i.new number $i CG_logfile $in/new_CG.prod$i.log pressure_flag $pres
