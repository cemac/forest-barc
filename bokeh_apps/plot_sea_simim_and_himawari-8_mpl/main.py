### SE Asia Sim. Im. and Himawari-8 Matplotlib example notebook

# This script demostrates creating plots of simulated satellite imagery and 
#  Himawari-8 imagery for SE Asia using the Matplotlib plotting library to
#  provide images to a Bokeh Server App.

## Setup notebook
# Do module imports

import os
import datetime

import matplotlib
matplotlib.use('agg')

import iris
iris.FUTURE.netcdf_promote = True

import bokeh.plotting


import forest.util
import forest.plot

import simim_sat_control
import simim_sat_data

## Extract
# Extract data from S3. The data can either be downloaded in full before 
#  loading, or downloaded on demand using the /s3 filemount. This is 
#  controlled by the do_download flag.

bokeh_id = __name__
bucket_name = 'stephen-sea-public-london'
server_address = 'https://s3.eu-west-2.amazonaws.com'

fcast_time = '20180109T0000Z'
fcast_time_obj =  datetime.datetime.strptime(fcast_time, '%Y%m%dT%H%MZ')

do_download = True
use_s3_mount = False
use_jh_paths = True
base_dir = os.path.expanduser('~/SEA_data/')


SIMIM_KEY = 'simim'
HIMAWARI8_KEY = 'himawari-8'

# The datasets dictionary is the main container for the sim. im./Himawari-8
#  data and associated meta data. It is stored as a dictionary of dictionaries.
# The first layer of indexing selects the data type, for example Simulated 
#  Imagery or Himawari-8 imagery. Each of these will be populated with a cube
#  or data image array for each of the available wavelengths as well as 
#  asociated metadata such as file paths etc.

datasets = {SIMIM_KEY:{'data_type_name': 'Simulated Imagery'},
            HIMAWARI8_KEY:{'data_type_name': 'Himawari-8 Imagery'},
           }

# Himawari-8 imagery dict population

s3_base_str = '{server}/{bucket}/{data_type}/'

s3_base_sat = s3_base_str.format(server = server_address,
                                 bucket = bucket_name,
                                 data_type=HIMAWARI8_KEY)
s3_local_base_sat = os.path.join(os.sep, 's3', bucket_name, HIMAWARI8_KEY)
base_path_local_sat = os.path.join(base_dir,HIMAWARI8_KEY)
fnames_list_sat = {}
for im_type in simim_sat_data.HIMAWARI_KEYS.keys():
    fnames_list_sat[im_type] = \
        ['{im}_{datetime}.jpg'.format(im = simim_sat_data.HIMAWARI_KEYS[im_type],
                                      datetime = (fcast_time_obj + datetime.timedelta(hours = vt)).strftime('%Y%m%d%H%M'))
         for vt in range(12, 39, 3) ]

print('satellite filenames')
print(fnames_list_sat)

datasets[HIMAWARI8_KEY]['data'] = simim_sat_data.SatelliteDataset(HIMAWARI8_KEY,
                                                                  fnames_list_sat,
                                                                  s3_base_sat,
                                                                  s3_local_base_sat,
                                                                  use_s3_mount,
                                                                  base_path_local_sat,
                                                                  do_download,
                                                                  )

s3_base_simim = s3_base_str.format(server = server_address,
                                   bucket = bucket_name,
                                   data_type = SIMIM_KEY)
s3_local_base_simim = os.path.join(os.sep, 's3', bucket_name, SIMIM_KEY)
base_path_local_simim= os.path.join(base_dir,SIMIM_KEY)
fnames_list_simim = ['sea4-{it}_HIM8_{date}_s4{run}_T{time}.nc'.format(it=im_type, 
                                                                       date=fcast_time[:8], run=fcast_time[9:11], 
                                                                       time = vt)
               for vt in range(12, 39, 3) for im_type in ['simbt', 'simvis']]
time_list_simim =  [vt for vt in range(12, 39, 3) for im_type in ['simbt', 'simvis']]

datasets[SIMIM_KEY]['data'] = simim_sat_data.SimimDataset(SIMIM_KEY,
                                                          fnames_list_simim,
                                                          s3_base_simim,
                                                          s3_local_base_simim,
                                                          use_s3_mount,
                                                          base_path_local_simim,
                                                          do_download,
                                                          time_list_simim,
                                                          fcast_time_obj)


# Write Himawari-8 image data to Numpy arrays in a dictionary indexed by time
#  string


## Setup plots

plot_options = forest.util.create_satellite_simim_plot_opts()

# Set the initial values to be plotted
init_time = '201801091200'
init_var = 'I'
init_region = 'se_asia'
region_dict = forest.util.SEA_REGION_DICT

## Display plots

# Create a plot object for the left model display
plot_obj_left = forest.plot.ForestPlot(datasets,
                                       plot_options,
                                       'plot_left' + bokeh_id,
                                       init_var,
                                       'simim',
                                       init_region,
                                       region_dict,
                                       simim_sat_data.UNIT_DICT,
                                       )

plot_obj_left.current_time = init_time
colorbar = plot_obj_left.create_colorbar_widget()
bokeh_img_left = plot_obj_left.create_plot()

# Create a plot object for the right model display
plot_obj_right = forest.plot.ForestPlot(datasets,
                                        plot_options,
                                        'plot_right' + bokeh_id,
                                        init_var,
                                        'himawari-8',
                                        init_region,
                                        region_dict,
                                        simim_sat_data.UNIT_DICT,
                                        )

plot_obj_right.current_time = init_time
bokeh_img_right = plot_obj_right.create_plot()

plot_obj_right.link_axes_to_other_plot(plot_obj_left)

plot_list1 = [plot_obj_left, plot_obj_right]
bokeh_imgs1 = [bokeh_img_left, bokeh_img_right]
control1 = simim_sat_control.SimimSatControl(datasets, 
                                             init_time, 
                                             fcast_time_obj, 
                                             plot_list1, 
                                             bokeh_imgs1,
                                             colorbar,
                                            )

print('         ', __file__.split('/')[-2])

try:
    bokeh_mode = os.environ['BOKEH_MODE']
except:
    bokeh_mode = 'server'    
    
if bokeh_mode == 'server':
    bokeh.plotting.curdoc().add_root(control1.main_layout)
elif bokeh_mode == 'cli':
    bokeh.io.show(control1.main_layout)

bokeh.plotting.curdoc().title = 'Model simulated imagery vs Himawari-8'    