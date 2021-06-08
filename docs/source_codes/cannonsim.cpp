#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <strings.h>
#include <math.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

double gravity, mass, velocity, angle, height, air_resistance, time_step;

static void usage(const char *argv0)
{
    fprintf(stderr, "Usage: %s [-i input dir path][-o output dir path]\n", argv0);
    exit(EXIT_FAILURE);
}
void launch(double* out_dist, double*  out_vx, double*  out_vy)
{
    double x = 0.0;
    double y = height;
    double vx = velocity * sin(angle);
    double vy = velocity * cos(angle);
    while (y > 0.0)
    {
        vy -= gravity * mass * time_step;
        vx -= vx * air_resistance * time_step;
        vy -= vy * air_resistance * time_step;
        x += vx * time_step;
        y += vy * time_step;

    }
    *out_dist = x;
    *out_vx = vx;
    *out_vy = vy;

}
int main(int argc, char **argv)
{

    char const *input_dir = "input_files";
    char const *output_dir = "output_files";

    // parse input arguments
    int opt;
    while ((opt = getopt(argc, argv, "i:o:")) != -1)
    {
        switch (opt)
        {
        case 'i':
            input_dir = optarg;
            break;
        case 'o':
            output_dir = optarg;
            break;
        default:
            usage(argv[0]);
        }
    }

    // read input parameters from simsetting.csv
    char simsetting_file[1024];
    sprintf (simsetting_file, "%s/%s", input_dir, "simsetting.txt");
    FILE *fp;
    char line[256];
    fp = fopen(simsetting_file, "r");
    if (fp == NULL)
    {
        fprintf(stderr, "Error reading file\n");
        return 1;
    }
    int i = 0;
    char name[64];
    double value;

    while (fscanf(fp, "\"%64[^\"]\",%lf", name, &value) == 2)
    {
        if (strcasecmp(name, "gravity") == 0)
            gravity = value;
        else if (strcasecmp(name, "mass") == 0)
            mass = value;
        else if (strcasecmp(name, "mass") == 0)
            mass = value;
        else if (strcasecmp(name, "velocity") == 0)
            velocity = value;
        else if (strcasecmp(name, "angle") == 0)
            angle = value;
        else if (strcasecmp(name, "height") == 0)
            height = value;
        else if (strcasecmp(name, "air_resistance") == 0)
            air_resistance = value;
        else if (strcasecmp(name, "time_step") == 0)
            time_step = value;
        else
        {
            fprintf(stderr, "Error : Input args %s in simsetting.txt file is not valid !\n", name);
            return 1;
        }

        while ((fgetc(fp) != '\n') && (!feof(fp)))   { /* do nothing */ }
    }
    fclose(fp);

    // run simulation
    double out_dist, out_vx, out_vy;
    launch(&out_dist, &out_vx, &out_vy);

    // check if output_dir is exists
    struct stat st = {0};
    if (stat(output_dir, &st) == -1)
    {
        mkdir(output_dir, 0700);
    }
    // Write distance travelled to output csv file
    char output_file[1024];
    sprintf (output_file, "%s/%s", output_dir, "c_output.txt");
    fp = fopen(output_file, "w");
    fprintf(fp, "Dist,lastvx,lastvy\n");
    fprintf(fp, "%lf,%lf,%lf", out_dist, out_vx, out_vy);
    fclose(fp);
}