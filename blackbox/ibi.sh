#!/bin/sh

in=$4 #../python
atom=$1 #../python
out=$5 #../python
ibi_script_dir=../python
i=$2
pres=$3
lammps_data_file=lammps_data_file

python $ibi_script_dir/IBI.py lammps_input_file $in/in.CG.lammps lammps_output_file $out/in.CG.lammps LAMMPS_data_file $atom/$lammps_data_file lammps_rdf_file $in/tmp.$i.rdf correct_rdf_base $atom/rdf potential_base $in/pot.$i.new number $i CG_logfile $in/new_CG.prod$i.log pressure_flag $pres
