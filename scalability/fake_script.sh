#! /bin/bash

#SBATCH -J VECMA
#SBATCH -p SKL-16c_edr-ib1_192gb_2666
#SBATCH --oversubscribe
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=100
#SBATCH -w genji253
#SBATCH --time=30:00


echo "The Job is starting !!"
sleep 15
echo "Job done !!"
