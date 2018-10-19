## tmdd_network

### extracting a tmdd network from aimsun

Dependencies: python 2.

Load an aimsun model. Note that this uses Aimsun Next 8.2.0. If using a different version of Aimsun, you should modify the location where the `.json` will be written.

In Aimsun, in the Project Panel right click `SCRIPTS` and select the option to create a new python script. Right click the new script created to access its properties. Under the settings tab, opt to read from external file and select the python file named `aimsun_to_tmdd.py`. When you execute the script, a `.json` file containing the tmdd will be written to `%APPDATA%/roaming/Aimsun/Aimsun Next/8.2.0/shared`. 

### correcting distortion

Dependencies: numpy, python 3.

Manually collect pairs of control points from the aimsun model and its respective location in the target data set. Points from aimsun should be saved in `aimsun_points.csv`, in the format `longitude, latitude`. points from the google tileset should be saved in `google_points`, using the same format.

Run `correct_distortion.py -horizontal <horizontal_zones> -vertical <vertical_zones>`. `-horizontal, -vertical` are required fields, specifying how the network should be segmented. You will see a print out of boxes representing the way the map has been divided, as well as how many manually selected control points are within each segment. We have achieved good results with 2 horizontal zones and 1 vertical zone.

All uncorrected .json files in the `/tmdd_network/data` subdirectory will be corrected and written to a new file.

If you would like the .json to be formatted for TMDD, make sure `FORMAT` is set to `True`. This means that coordinates will be output as an integer with seven digits of precision. For example, `34.12141827922749` will be represented as `341214183`. 

### export geoposition as csv

Dependencies: shapely. (See onboarding_instructions.txt in Box if you need help installing this.)

Run `export_coordinate.csv`. All corrected `.json` files in the `data` subdirectory will have a corresponding `.csv` file written.