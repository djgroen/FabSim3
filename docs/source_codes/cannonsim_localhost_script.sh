# change directory to where application is stored
cd ~/FabSim3/results/cannon_app_localhost_1
/bin/true || true

OUTPUT_DIR="output_files"
INPUT_DIR="input_files"

# run c program
gcc cannonsim.cpp -o cannonsim -lm
./cannonsim

# run python program
python cannonsim.py

# run java program
export CLASSPATH='java_libs/commons-cli-1.3.1.jar:.'
javac cannonsim.java
java cannonsim

# show output results
echo "Output results for python program :"
cat $OUTPUT_DIR/py_output.txt

echo "Output results for C program :"
cat $OUTPUT_DIR/c_output.txt

echo "Output results for Java program :"
cat $OUTPUT_DIR/java_output.txt 
