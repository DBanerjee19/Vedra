import numpy as np
import subprocess
import json


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





#*************  4 input network configurations (choose one and run) **************#
## Input 1: [[Pre1, Norm1], [Pre2, FWA1]]
no_of_slices = 4
no_of_part = 2
no_of_serv = 3
sl_m = [2, 3, 2, 3]
sl_t_win = [27, 42, 28, 21]  ## Solver output
service_slice_map = [[0, 2], [1], [3]]
slice_part_map = [0, 0, 1, 1]
access_in_mult_part = [1, 0, 0]


## Input 2:  [[Pre1, Norm1], [Pre2, Norm2, FWA1], [Pre3, FWA2]]
no_of_slices = 7
no_of_part = 3
no_of_serv = 3
sl_m = [2, 3, 2, 2, 3, 2, 3]
sl_t_win = [29, 35, 29, 35, 23, 29, 23]  ## Solver output
service_slice_map = [[0, 2, 5], [1, 3], [4, 6]]  # (Pre, Norm, FWA)
slice_part_map = [0, 0, 1, 1, 1, 2, 2]
part_slice_map = [[0, 1], [2, 3, 4], [5, 6]]
access_in_mult_part = [1, 1, 1]  

## Input 3:  [[Pre1, Norm1, URLLC1], [Pre2, FWA2, URLLC2, mMTC1], [Norm2, FWA2, mMTC2]]
no_of_slices = 10
no_of_part = 3
no_of_serv = 5
sl_m = [2, 3, 4, 2, 3, 3, 3, 3, 3, 3]
sl_t_win = [62, 68, 27, 39, 33, 27, 21, 68, 33, 21]  ## Solver output
service_slice_map = [[0, 3], [1, 7], [4, 8], [2, 5], [6, 9]]  # (Pre, Norm, FWA, URLLC, mMTC)
slice_part_map = [0, 0, 0, 1, 1, 1, 1, 2, 2, 2]
part_slice_map = [[0, 1, 2], [3, 4, 5, 6], [7, 8, 9]]
access_in_mult_part = [1, 1, 1, 1, 1]  


## Input 4:  [[Pre1, Norm1, URLLC1], [FWA1, URLLC2, mMTC1], [Pre2, Norm2, FWA2, mMTC2], [Pre3, Norm3, URLLC3]]
no_of_slices = 13
no_of_part = 4
no_of_serv = 5
sl_m = [2, 3, 3, 3, 3, 3, 2, 3, 3, 4, 2, 3, 3]
sl_t_win = [44, 51, 29, 36, 23, 22, 42, 53, 35, 21, 43, 50, 28]  ## Solver Output
service_slice_map = [[0, 6, 10], [1, 7, 11], [3, 8], [2, 12], [5, 9]]  # (Pre, Norm, FWA, URLLC, mMTC)
slice_part_map = [0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3]
part_slice_map = [[0, 1, 2], [3, 4, 5], [6, 7, 8, 9], [10, 11, 12]]
access_in_mult_part = [1, 1, 1, 1, 1] 




timesteps = 60000
total_PRB = 15000   

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



