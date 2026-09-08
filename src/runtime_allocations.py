import numpy as np
import subprocess
import json
import os
import sys

# argument contains input filename
if len(sys.argv) > 1:
    input_filename = sys.argv[1]

#  path to the 'testcases' folder
base_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_dir, '..', 'testcases', input_filename)

config = {}

if os.path.exists(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            
            var_name, var_value = line.split('=', 1)
            # load directly into the dictionary
            config[var_name.strip()] = eval(var_value.strip())

# variables
no_of_slices = config['no_of_slices']
no_of_part = config['no_of_part']
no_of_serv = config['no_of_serv']
sl_m = config['sl_m']
sl_t_win = config['sl_t_win']
service_slice_map = config['service_slice_map']
slice_part_map = config['slice_part_map']
access_in_mult_part = config['access_in_mult_part']
total_PRB = config['total_PRB']




def create_sparse_array(length, target_ones_pct, initial_zeros):
    # initializing  array with zeros
    arr = np.zeros(length, dtype=int)
    
    # calculating remaining slots after the initial zero buffer
    remaining_length = length - initial_zeros
    num_ones = int(length * target_ones_pct)
    
    if num_ones <= 0:
        return arr

    # generating non-clustering positions using random spacing
    avg_gap = remaining_length / num_ones 
    
    # creating random offsets that fluctuate around the average gap
    gaps = np.random.normal(loc=avg_gap, scale=0.5, size=num_ones)
    gaps = np.clip(gaps, 2, None).astype(int) # Min gap of 2 forces at least one '0' between '1's
    
    # calculating absolute indices for the 1s
    ones_indices = initial_zeros + np.cumsum(gaps)
    
    # filtering out indices that overshoot array bounds
    ones_indices = ones_indices[ones_indices < length]
    
    # inserting the 1s into the array
    arr[ones_indices] = 1
    return arr

# timesteps for simulation
timesteps = 60000


sum_PRB = 0
for slc in range(no_of_slices):
    x = (int)(timesteps/sl_t_win[slc])
    sum_PRB += x * (int)(sl_t_win[slc]/sl_m[slc])


# Initialize user entry and leaving flag arrays
service_entry_array = np.zeros((no_of_serv, timesteps), dtype=int)
service_leave_array = np.zeros((no_of_slices, timesteps), dtype=int)

######################### Generating service data ##############################
for srv in range(no_of_serv):
    
    if srv == 0:
        subprocess.run(["python", "eMBB_Premium_userdata_generation.py", str(timesteps)], check=True)
        filename = "eMBB_Premium_userdata.txt"

    elif srv == 1:
        subprocess.run(["python", "eMBB_Normal_userdata_generation.py", str(timesteps)], check=True)
        filename = "eMBB_Normal_userdata.txt"

    elif srv == 2:
        subprocess.run(["python", "FWA_userdata_generation.py", str(timesteps)], check=True)
        filename = "FWA_userdata.txt"

    elif srv == 3:
        subprocess.run(["python", "URLLC_userdata_generation.py", str(timesteps)], check=True)
        filename = "URLLC_userdata.txt"

    elif srv == 4:
        subprocess.run(["python", "mMTC_userdata_generation.py", str(timesteps)], check=True)
        filename = "mMTC_userdata.txt"

    # Read the file content safely
    with open(filename, "r") as f:
        content = f.read()
        
        # extract the raw list string between the brackets [ ... ]
        raw_list_str = content.split(":")[-1].strip()
        
        # convert string representation of the list back into a Python list
        flag_array = json.loads(raw_list_str)
        
        # store it into  matrix
        service_entry_array[srv] = np.array(flag_array)


### Generate user leaving flags
for srv in range(no_of_serv):
    slices = service_slice_map[srv]
    for slc in slices:
        ## eMBB Pre
        if srv==0:
            service_leave_array[slc] = create_sparse_array(length=timesteps, target_ones_pct=0.20, initial_zeros=50)
        ## eMBB Norm
        elif srv==1:
            service_leave_array[slc] = create_sparse_array(length=timesteps, target_ones_pct=0.33, initial_zeros=50)
        ## FWA, URLLC
        elif srv==2 or srv==3:
            service_leave_array[slc] = create_sparse_array(length=timesteps, target_ones_pct=0.15, initial_zeros=50)
        ## mMTC
        elif srv==4:
            service_leave_array[slc] = create_sparse_array(length=timesteps, target_ones_pct=0.1, initial_zeros=50)



## Initialization
#************  slices ********************
sl_usr = np.zeros(no_of_slices, dtype=int)
sl_usg = np.zeros(no_of_slices, dtype=int)
sl_resi = np.zeros(no_of_slices, dtype=int)
sl_E = np.zeros(no_of_slices, dtype=int)

total_slices_demand = []
total_slices_allocation = []
DAR = []


#************  PARTITIONS ********************
part_share = np.zeros(no_of_part, dtype=int)

#************  RESIDUAL PARTITION  ********************
resi_part_share = total_PRB
resi_part_overuse = 0

## Initial alloactionto slices and partitions
for slc in range(no_of_slices):
    sl_resi[slc] = (int)(sl_t_win[slc]/sl_m[slc])
    which_part = slice_part_map[slc]
    part_share[which_part] += sl_resi[slc]
    resi_part_share -= sl_resi[slc]

time_arr = []
top_up_ticks = []
ramp_down_ticks = []
Resi_part_share_data = []
PRB_share_pre1 = 0

# 1. Clear the old logs ONCE at the start of your program
with open("output.txt", "w") as f:
    f.write("=== SIMULATION LOG START ===\n")

############################  SIMULATION  #############################
for t in range(timesteps):


    #**********************  Assigning or de-assigning services to slices **************#
    # assigning or arrival
    for serv in range(no_of_serv):

        which_slice = service_slice_map[serv]

        if service_entry_array[serv][t] == 1 and resi_part_overuse == 0:

            # if UE  has access in only one partition
            if access_in_mult_part[serv] == 0:
                which_slice = which_slice[0]
                sl_usr[which_slice] += 1

                if t % sl_t_win[which_slice] == 1:
                    sl_E[which_slice] = 1
                else:
                    sl_E[which_slice] += 1
                
                if sl_usr[which_slice] % sl_m[which_slice] == 1:
                    sl_usg[which_slice] += 1
                    sl_resi[which_slice] -= 1
            else:
                min_usr = timesteps+1
                sl_ind = -1
                for slc in service_slice_map[serv]:
                    if sl_usr[slc] < min_usr:
                        min_usr = sl_usr[slc]
                        sl_ind = slc

                which_slice = sl_ind
                sl_usr[which_slice] += 1

                if t % sl_t_win[which_slice] == 1:
                    sl_E[which_slice] = 1
                else:
                    sl_E[which_slice] += 1
                
                if sl_usr[which_slice] % sl_m[which_slice] == 1:
                    sl_usg[which_slice] += 1
                    sl_resi[which_slice] -= 1
            
        else:
            for slc in which_slice:
                if t % sl_t_win[slc] == 1:
                    sl_E[slc] = 0

    # de-assigning on removal
    for slc in range(no_of_slices):
        if service_leave_array[slc][t] == 1 and sl_usr[slc]>0:
            sl_usr[slc] -= 1

            if sl_usr[slc] == 0 or sl_usr[slc] % sl_m[slc] == 0:
                sl_usg[slc] -= 1
                sl_resi[slc] += 1


    ###########   TOP-UP  AND  RAMP-DOWN IN SLICES   ##########
    net_part_top_up =  np.zeros(no_of_part, dtype=int)
    net_part_ramp_down = np.zeros(no_of_part, dtype=int)

    which_part_prev = 0
    ct_part  = 0
    top_up_or_ramp_down_flag = 0
    

    for slc in range(no_of_slices):

        which_part = slice_part_map[slc]
        if (which_part_prev != which_part):
            ct_part += 1

        ############  TOP-UP SLICE #################
        if resi_part_overuse == 0 and t % sl_t_win[slc] == 0 and t!=0 and sl_resi[slc] < (int)(sl_t_win[slc]/sl_m[slc]):
            sl_resi[slc] += (int)(sl_t_win[slc]/sl_m[slc])
            net_part_top_up[ct_part] += (int)(sl_t_win[slc]/sl_m[slc])

            top_up_or_ramp_down_flag = 1


        ###########  RAMP-DOWN SLICE  ##################
        if t % sl_t_win[slc] == 0 and t!=0 and sl_resi[slc] >= 2*(int)(sl_t_win[slc]/sl_m[slc]) and sl_E[slc] ==0:
            # sl_usg[slc] -= (int)(sl_t_win[slc]/sl_m[slc])
            sl_resi[slc] -= (int)(sl_t_win[slc]/sl_m[slc])
            net_part_ramp_down[ct_part] += (int)(sl_t_win[slc]/sl_m[slc])

            top_up_or_ramp_down_flag = 1

        which_part_prev = which_part


    total_part_top_up = 0
    total_part_ramp_down = 0

    ######  TOP-UP AND RAMP-DOWN IN PARTITIONS  #############
    for prt in range(no_of_part):
        if (net_part_top_up[prt] > net_part_ramp_down[prt]):
            part_share[prt] += net_part_top_up[prt]
            total_part_top_up += net_part_top_up[prt]

        elif (net_part_top_up[prt] < net_part_ramp_down[prt]):
            part_share[prt] -= net_part_ramp_down[prt]
            total_part_ramp_down += net_part_ramp_down[prt]

    #######  ALLOCATIONS AND DE-ALLOCATIOSN FROM THE RESIDUAL PARTITION ######
    ## Residual partition: PRBS de-allocated
    if total_part_top_up > total_part_ramp_down:
        resi_part_share -= total_part_top_up - total_part_ramp_down
    ### Residual partition: PRBs allocated
    elif total_part_top_up < total_part_ramp_down:
        resi_part_share += total_part_ramp_down - total_part_top_up


    ###### RESIDUAL PARTITION OVERUSE CONDITION  #########
    if resi_part_share < (int)(2*total_PRB/5):
        resi_part_overuse = 1
    else:
        resi_part_overuse = 0


