## tmdd_network

### extracting a tmdd network from aimsun

load an aimsun model. import the python file named `aimsun_to_tmdd.py`. run the python file from the aimsun python environment. a `.json` file containing the tmdd will be written to `~/somewhere`. 

### correcting distortion

manually collect pairs of control points from the aimsun model and it's respective location in the target data set. points from aimsun should be saved in `aimsun_points.csv`, in the format `longitude, latitude`. points from the google tileset should be saved in `google_points`, using the same format.

run `correct_distortion.py -h <horizontal_zones> -v <vertical_zones>`. `-h, -v` are required fields, specifying how the network should be segmented.

the corrected `.json` files will be written into the `~/tmdd_network/data` subdirectory. 

### export geoposition as csv

run `export_coordinate.csv`. all corrected `.json` files in the `data` subdirectory will have a corresponding `.csv` file written.