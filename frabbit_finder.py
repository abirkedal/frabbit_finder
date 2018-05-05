# I normally run this from a screen instance using:
# stdbuf -oL nohup python ~/Python/frabbit_finder.py &> output.20180419.txt
# I realize the nohup is redundant with what screen gives me.

import datetime
import time
import pytz
import numpy as np
import os
from subprocess import call
from PIL import Image

run_flag = True
counter = 0
# Use this if you are starting during the night 
exposure_time = 3000000
# use this if you are starting during the day 
exposure_time = 150 
exposure_time_min = 1e-10
exposure_time_max = 6600000
exposure_time = 70 

exposure_time_adjustment_fraction = 0.025
exposure_time_adjustment_factor = 1.0 + exposure_time_adjustment_fraction
exposure_time_adjustment_factor_min = 1.001
exposure_time_adjustment_factor_max = 2.0

brightness_min = 71
brightness_max = 160 

# Here we see if the brightness, etc are acceptable
def adjust_camera_parameters(exposure_time, exposure_time_adjustment_factor):
    # This first conditional is to try and keep the brightness from flip-flopping
    if (b < brightness_min and old_b > brightness_max) or (b > brightness_max and old_b < brightness_min):
	exposure_time_adjustment_factor = 0.5 * exposure_time_adjustment_factor + 0.5
    else:
        # hysteresis to make it shrink faster than it grows
        if (b < brightness_min and old_b < brightness_min) or (b > brightness_max and old_b > brightness_max):
	    exposure_time_adjustment_factor = exposure_time_adjustment_factor + 0.25 * exposure_time_adjustment_fraction

        # Should we return things to normal now?

    # if ((b < brightness_min and old_b > brightness_max) or (b > brightness_max and old_b < brightness_min)) and exposure_time != old_exp_time:
    #     # exposure_time = 0.5 * (exposure_time + old_exp_time)
    #     # Try interpolating
    #     a0 = (b - old_b)/(exposure_time - old_exp_time)
    #     a1 = (b * old_exp_time - old_b * exposure_time)/(old_exp_time - exposure_time)
    #     b_ideal = 0.5 * (brightness_min + brightness_max)
    #     exposure_time = (b_ideal - a1) / a0
    # el
    if b < brightness_min:
        exposure_time = exposure_time * exposure_time_adjustment_factor
    elif b > brightness_max:
        exposure_time = exposure_time / exposure_time_adjustment_factor

    # clip the exposure time if necessary
    if exposure_time < exposure_time_min:
	exposure_time = exposure_time_min
    if exposure_time > exposure_time_max:
	exposure_time = exposure_time_max

    if exposure_time_adjustment_factor > exposure_time_adjustment_factor_max:
        exposure_time_adjustment_factor = exposure_time_adjustment_factor_max
    if exposure_time_adjustment_factor < exposure_time_adjustment_factor_min:
        exposure_time_adjustment_factor = exposure_time_adjustment_factor_min

    return (exposure_time, exposure_time_adjustment_factor)

# One nice way to view the plots is with the feh command:
# feh -d -R 15 -S filename /home/pi/FrabbitPhotos/
# This way has better zoom settings
# feh --keep-zoom-vp --zoom fill -d -R 15 -S filename /home/pi/FrabbitPhotos/

old_exp_time = exposure_time
old_b = 0.5 * (brightness_min + brightness_max)

while run_flag:
    # Grab a timestamp string to use in the filename
    time_string = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime('%Y%m%d%H%M%S')
    
    output_fn = "/home/pi/FrabbitPhotos/frabbit."+time_string+".jpg"
    
    # Take the picture with the webcam and store it, takes about 2 seconds
    # call(["fswebcam","-d","/dev/video0","-r","1280x720","--no-banner","/home/pi/FrabbitPhotos/frabbit."+time_string+".jpg"])

    # Take the picture with the picamera and store it, takes about 5 seconds
    # call(["raspistill","-w","640","-h","480","-o","/home/pi/FrabbitPhotos/frabbit."+time_string+".jpg"])

    # This one takes a picture w raspberry pi camera with a long exposure time and then stores it
    call(["raspistill","-w","1640","-h","1232","-ISO", "800", "-ss", str(exposure_time), "-br", "80", "-co", "100","-o", output_fn])

    im = Image.open(output_fn)
    s = os.path.getsize(output_fn)
    b = np.mean(im) 
    print(time_string, b, s, exposure_time, old_b, old_exp_time, exposure_time_adjustment_factor)

    # Remove the file if the brightness is wrong
    if (b < brightness_min) or (b > brightness_max):
	# Remove the file
	print('The brightness is bad, removing the file')
	os.remove(output_fn)
    else:
	# Wait 10 seconds so there are about 15 seconds between pictures
    	time.sleep(10)

    old_exp_time = exposure_time
    (exposure_time, exposure_time_adjustment_factor) = adjust_camera_parameters(exposure_time, exposure_time_adjustment_factor)

    print(exposure_time, exposure_time_adjustment_factor)
    
    old_b = b
    
    # Every once in a while, check for old pictures and delete them
    # if counter % 100 == 0:
        # check for old pictures to delete
    counter += 1
