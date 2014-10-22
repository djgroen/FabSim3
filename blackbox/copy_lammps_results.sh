#!/bin/sh

out_dir=$1
work_dir=$2
i=$3

cp $out_dir/in.CG.lammps $work_dir/in.CG.lammps.$i
cp $out_dir/new_CG.prod$i.log $work_dir/
cp $out_dir/tmp.$i.rdf $work_dir/

