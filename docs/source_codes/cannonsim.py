import matplotlib
matplotlib.use('Agg')

from math import sin, cos
from os import path, makedirs
import csv
import argparse
import matplotlib.pyplot as plt


def launch(gravity, mass, velocity, angle, height,
           air_resistance, time_step):
    x = 0.0
    y = height
    vx = velocity * sin(angle)
    vy = velocity * cos(angle)

    out_x = []
    out_y = []
    while y > 0.0:
        # Euler integrate
        vy -= gravity * mass * time_step
        vx -= vx * air_resistance * time_step
        vy -= vy * air_resistance * time_step
        x += vx * time_step
        y += vy * time_step
        out_x.append(x)
        out_y.append(y)

    out_dist = x
    out_vx = vx
    out_vy = vy
    return out_dist, out_vx, out_vy, out_x, out_y


if __name__ == "__main__":

    # python cannonsim.py
    # python cannonsim.py --input_dir=<xxx> --output_dir=<xx>

    # Instantiate the parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dir',
                        action="store", default='input_files')
    parser.add_argument('--output_dir',
                        action="store", default='output_files')

    args = parser.parse_args()
    input_dir = args.input_dir
    output_dir = args.output_dir

    # read input parameters from simsetting.csv
    input_file = path.join(input_dir, "simsetting.txt")
    if path.isfile(input_file):
        with open(input_file, newline='') as csvfile:
            values = csv.reader(csvfile)
            for row in values:
                if len(row) > 0:  # skip empty lines in csv
                    if row[0][0] == "#":
                        pass
                    elif row[0].lower() == "gravity":
                        gravity = float(row[1])
                    elif row[0].lower() == "mass":
                        mass = float(row[1])
                    elif row[0].lower() == "velocity":
                        velocity = float(row[1])
                    elif row[0].lower() == "angle":
                        angle = float(row[1])
                    elif row[0].lower() == "height":
                        height = float(row[1])
                    elif row[0].lower() == "air_resistance":
                        air_resistance = float(row[1])
                    elif row[0].lower() == "time_step":
                        time_step = float(row[1])

    # run simulation
    [out_dist, out_vx, out_vy, out_x, out_y] = launch(gravity, mass, velocity, angle, height,
                                                      air_resistance, time_step)
    # Write distance travelled to output csv file
    # check if output_dir is exists
    if not path.exists(output_dir):
        makedirs(output_dir)
    output_file = path.join(output_dir, "py_output.txt")

    with open(output_file, "w") as f:
        f.write("Dist,lastvx,lastvy\n")
        f.write("%f,%f,%f" % (out_dist, out_vx, out_vy))

    with open(output_file, "r") as f:
        print(f.read())

    # plotting the results
    output_png = path.join(output_dir, "py_output.png")
    fig = plt.figure()
    ax = plt.axes()
    ax.plot(out_x, out_y)
    plt.savefig(output_png, dpi=400)
