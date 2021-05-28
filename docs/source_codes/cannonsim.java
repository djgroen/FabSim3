import org.apache.commons.cli.*;
import java.io.*;
import java.util.*;
import java.lang.Math;
//import java.io.File;
public class cannonsim
{
	public static String input_dir = "input_files";
	public static String output_dir = "output_files";

	// input simulation parameters
	public static double gravity, mass, velocity, angle, height, air_resistance, time_step;
	// output simulation results
	public static double out_dist, out_vx, out_vy;

	public static void parse_args(String[] args)
	{
		Options options = new Options();
		Option input_option = Option.builder("i")
		                      .longOpt( "input_dir" )
		                      .hasArg()
		                      .required(false)
		                      .build();
		options.addOption( input_option );

		Option output_option = Option.builder("o")
		                       .longOpt( "output_dir" )
		                       .hasArg()
		                       .required(false)
		                       .build();
		options.addOption( output_option );

		// # Instantiate the parser
		CommandLineParser parser = new DefaultParser();

		try {

			CommandLine line = parser.parse( options, args );
			if (line.hasOption( "input_dir" )) {
				input_dir = line.getOptionValue("input_dir");
			}
			if (line.hasOption( "output_dir" )) {
				output_dir = line.getOptionValue("output_dir");
			}
		} catch (ParseException exp) {
			System.out.println(exp.getMessage());
			System.exit(1);
		}
	}
	public static void read_simsetting()
	{
		String simsetting_file = new File(input_dir, "simsetting.txt").toString();

		try {
			BufferedReader reader = new BufferedReader(new FileReader(simsetting_file));
			String line = reader.readLine();
			while (line != null) {
				String data[] = line.replace("\"", "").split(",");
				String name = data[0];
				double value = Double.parseDouble(data[1]);

				if (name.equalsIgnoreCase("gravity")) {
					gravity = value;
				} else if (name.equalsIgnoreCase("mass")) {
					mass = value;
				} else if (name.equalsIgnoreCase("velocity")) {
					velocity = value;
				} else if (name.equalsIgnoreCase("angle")) {
					angle = value;
				} else if (name.equalsIgnoreCase("height")) {
					height = value;
				} else if (name.equalsIgnoreCase("air_resistance")) {
					air_resistance = value;
				} else if (name.equalsIgnoreCase("time_step")) {
					time_step = value;
				}


				line = reader.readLine();
			}
			reader.close();
		} catch (FileNotFoundException ex) {
			System.out.println(ex);
		} catch (IOException ex) {
			System.out.println(ex);
		}


	}
	public static void launch()
	{
		double x = 0.0;
		double y = height;
		double vx = velocity * Math.sin(angle);
		double vy = velocity * Math.cos(angle);
		while (y > 0.0) {
			vy -= gravity * mass * time_step;
			vx -= vx * air_resistance * time_step;
			vy -= vy * air_resistance * time_step;
			x += vx * time_step;
			y += vy * time_step;

		}

		out_dist = x;
		out_vx = vx;
		out_vy = vy;
	}

	public static void write_output_results()
	{
		// create output folder if it does not exist
		File fp = new File(output_dir, "java_output.txt");
		fp.getParentFile().mkdirs();
		//FileWriter fr = new FileWriter(fp);
		try {
			FileWriter fr = new FileWriter(fp);
			fr.write("Dist,lastvx,lastvy\n");
			fr.write(String.format("%.6f", out_dist) + "," +
			         String.format("%.6f", out_vx) + "," +
			         String.format("%.6f", out_vy) + "\n");
			fr.close();

		} catch (IOException e) {
			System.err.print("Something went wrong");
		}



	}
	public static void main(String[] args) throws Exception
	{
		// parse input arguments
		parse_args(args);

		// read input parameters from simsetting.csv
		read_simsetting();

		// run simulation
		launch();

		// save output results
		write_output_results();

	}

}