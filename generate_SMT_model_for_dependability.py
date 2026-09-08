from z3 import *
import numpy as np
from itertools import product
import subprocess

total_PRB = 15000

#*************  4 input network configurations (choose one and run) **************#
#$ Input 1:  [[Pre1, Norm1], [Pre2, FWA1]]
no_of_slices = 4
no_of_part = 2
no_of_serv = 3
sl_m = [2, 3, 2, 3]
slice_part_map = [0, 0, 1, 1]
part_slice_map = [[0, 1], [2, 3]]
user_dist_map = [[1], [0, 2], [3]]


## Input 2:  [[Pre1, Norm1], [Pre2, Norm2, FWA1], [Pre3, FWA2]]
no_of_slices = 7
no_of_part = 3
no_of_serv = 3
sl_m = [2, 3, 2, 2, 3, 2, 3]
slice_part_map = [0, 0, 1, 1, 1, 2, 2]
part_slice_map = [[0, 1], [2, 3, 4], [5, 6]]
user_dist_map = [ [1, 3], [0, 2, 5], [4, 6]]  # ( Norm, Pre, FWA)


## Input 3:  [[Pre1, Norm1, URLLC1], [Pre2, FWA2, URLLC2, mMTC1], [Norm2, FWA2, mMTC2]]
no_of_slices = 10
no_of_part = 3
no_of_serv = 5
sl_m = [2, 3, 4, 2, 3, 3, 3, 2, 3, 3]
slice_part_map = [0, 0, 0, 1, 1, 1, 1, 2, 2, 2]
part_slice_map = [[0, 1, 2], [3, 4, 5, 6], [7, 8, 9]]
user_dist_map = [[1, 7], [0, 3], [4, 8], [2, 5], [6, 9]]  # ( Norm, Pre, FWA, URLLC, mMTC)

## Input 4:  [[Pre1, Norm1, URLLC1], [FWA1, URLLC2, mMTC1], [Pre2, Norm2, FWA2, mMTC2], [Pre3, Norm3, URLLC3]]
no_of_slices = 13
no_of_part = 4
no_of_serv = 5
sl_m = [2, 3, 3, 3, 3, 3, 2, 3, 3, 4, 2, 3, 3]
slice_part_map = [0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3]
part_slice_map = [[0, 1, 2], [3, 4, 5], [6, 7, 8, 9], [10, 11, 12]]
user_dist_map = [[1, 7, 11], [0, 6, 10], [3, 8], [2, 12], [5, 9]]       # ( Norm, Pre, FWA, URLLC,  mMTC)



## 'generated_SMT_model.py' contains the SMT model that is genertaed by this wrapper file
fp = open('generated_SMT_model.py','w')


#===============================================================================
#    This is a Wrappr File Writing SMT-Clauses to another file
#===============================================================================
clause="###Gen starts here\n"
clause+="from z3 import *\n"
clause+='''from numpy import *
import time\n'''
clause+="from time import process_time\n\n"
clause+="t1_start = process_time()\n\n\n"

clause+= f'''no_of_slices = IntVal({no_of_slices})
no_of_partitions = IntVal({no_of_part})

sl_m = {sl_m}


s = Solver()     # solver is defined   

sl_top_up_sig = [ Bool("sl_top_up_sig_%s" % i)   for i in range(no_of_slices.as_long()) ]
sl_ramp_down_sig = [ Bool("sl_ramp_down_sig_%s" % i)   for i in range(no_of_slices.as_long()) ]

sl_share0 = [ Int("sl_share0_%s" % i) for i in range(no_of_slices.as_long()) ]
sl_share1 = [ Int("sl_share1_%s" % i) for i in range(no_of_slices.as_long()) ]

sl_t_win = [ Int("sl_t_win_%s" % i) for i in range(no_of_slices.as_long()) ]
# sl_m = [ Int("sl_m%s" % i) for i in range(no_of_slices.as_long()) ]

part_share0 = [ Int("part_share0_%s" % i) for i in range(no_of_partitions.as_long()) ]  
part_share1 = [ Int("part_share1_%s" % i) for i in range(no_of_partitions.as_long()) ]

Resi_share0 = Int("Resi_share0") 
Resi_share1 = Int("Resi_share1")  

# total_PRB = Int("total_PRB") 
\n\n\n'''


for slc in range(no_of_slices):
    clause+=f's.add( If(sl_top_up_sig[{slc}]==True, 1, 0) +  If(sl_ramp_down_sig[{slc}]==True, 1, 0) <= 1)\n'
    clause+=f's.add(sl_share0[{slc}] >= 0)\n'
    clause+=f's.add(sl_share1[{slc}] >= 0)\n'
    clause+=f's.add(sl_t_win[{slc}] > 20)\n'

for serv in range(no_of_serv-1):

    ## Windows
    slices = user_dist_map[serv]
    slices_after = user_dist_map[serv+1]
  
    for slc1 in slices:
        clause+=f'\ns.add( '
        for slc2 in slices_after:
            clause+=f'sl_t_win[{slc1}] > sl_t_win[{slc2}] + 5, '
        clause+=f')'



for serv in range(no_of_serv):

    ## Windows
    slices = user_dist_map[serv]
    l = len(slices)   
    for slc_ct in range(l):
        clause+=f'\ns.add( '
        for slc2 in slices_after:
            if l>2:
                if slc_ct!=l-1:
                    clause+=f'sl_t_win[{slices[slc_ct]}] != sl_t_win[{slices[slc_ct+1]}], '
                else:
                    clause+=f'sl_t_win[{slices[slc_ct]}] != sl_t_win[{slices[0]}], '
            else:
                if slc_ct!=l-1:
                    clause+=f'sl_t_win[{slices[slc_ct]}] != sl_t_win[{slices[slc_ct+1]}], '
        clause+=f')'
        

for prt in range(no_of_part):
    clause+=f'\ns.add(part_share0[{prt}] >= 0)\n'
    clause+=f's.add(part_share1[{prt}] >= 0)\n'

clause+=f's.add(Resi_share0 >= 0)\n'
clause+=f's.add(Resi_share1 >= 0)\n\n\n'

fp.write(clause)



in_slice_ind = 0  # initial slice index
clause = "####### All possible top-up, ramp-down scenarios in slices #######\n\n"
for prt in range(no_of_part):

    clause += f"##***************** Partition {prt+1} ********************* \n\n"

    slices = part_slice_map[prt]
    no_of_repeat = len(slices)

    # adjusting initial slice index
    if prt!=0:
        in_slice_ind += len(part_slice_map[prt-1])

    # Generate all pairs from [0, 1, 2]:  # 0: none, 1: TU, 2: RD
    combinations = list(product([0, 1, 2], repeat=no_of_repeat))
    counting_constraints = 1

    ######################### Slices ##########################

    for comb in combinations:
        clause += f'## Type {counting_constraints} \n'
        clause += 's.add( Implies ( And ( '
        net_top_up = 0
        net_ramp_down = 0
        for ct in range(no_of_repeat):

            if comb[ct]==0:
                clause += f'''sl_top_up_sig[{in_slice_ind+ct}] == False, sl_ramp_down_sig[{in_slice_ind+ct}] == False, '''
            elif comb[ct]==1:
                clause += f'''sl_top_up_sig[{in_slice_ind+ct}] == True, '''
            elif comb[ct]==2:
                clause += f'''sl_ramp_down_sig[{in_slice_ind+ct}] == True, '''
        
        clause += '), \n'
        clause += 'And ( '

        for ct in range(no_of_repeat):

            if comb[ct]==0:
                clause += f'''sl_share1[{in_slice_ind+ct}] == sl_share0[{in_slice_ind+ct}], '''
            elif comb[ct]==1:
                clause += f'''sl_share1[{in_slice_ind+ct}] == sl_share0[{in_slice_ind+ct}] + (sl_t_win[{in_slice_ind+ct}] / {sl_m[in_slice_ind+ct]}), '''
            elif comb[ct]==2:
                clause += f'''sl_share1[{in_slice_ind+ct}] == sl_share0[{in_slice_ind+ct}] - (sl_t_win[{in_slice_ind+ct}] / {sl_m[in_slice_ind+ct]}), '''
        

        clause += f'''\n part_share1[{prt}] == part_share0[{prt}] '''
        for ct in range(no_of_repeat):

            if comb[ct]==1:
                clause += f'''+ (sl_share1[{in_slice_ind+ct}] - sl_share0[{in_slice_ind+ct}]) '''
            elif comb[ct]==2:
                clause += f'''- (sl_share0[{in_slice_ind+ct}] - sl_share1[{in_slice_ind+ct}]) '''

        clause += ') ) ) \n\n'

        counting_constraints += 1

fp.write(clause)



#############################  Partitions ###############################

clause = "\n\n####### All possible top-up, ramp-down scenarios in partitions #######\n\n"


# Generate all pairs from [0, 1, 2]:  # 0: none, 1: allocation, 2: de-allocation in partition
combinations = list(product([0, 1, 2], repeat=no_of_part))
counting_constraints = 1

for comb in combinations:
    clause += f'## Type {counting_constraints} \n'
    clause += 's.add( Implies ( And ( '
    net_top_up = 0
    net_ramp_down = 0
    for ct in range(no_of_part):

        if comb[ct]==0:
            clause += f'''part_share1[{ct}] == part_share0[{ct}],  '''
        elif comb[ct]==1:
            clause += f'''part_share1[{ct}] > part_share0[{ct}], '''
        elif comb[ct]==2:
            clause += f'''part_share1[{ct}] < part_share0[{ct}], '''
    
    clause += '), \n'
    clause += 'And ( Resi_share1 == Resi_share0 '

    for ct in range(no_of_part):
      
        if comb[ct]==1:
            clause += f'''- (part_share1[{ct}] - part_share0[{ct}]) '''
        elif comb[ct]==2:
            clause += f'''+ (part_share0[{ct}] - part_share1[{ct}]) '''
    

    clause += ') ) ) \n\n'

    counting_constraints += 1


clause += f'''s.add(Resi_share1 >= ((2*{total_PRB})/5)) \n'''
clause += f'''s.add(Resi_share0 >= ((2*{total_PRB})/5)) \n'''

clause += '''\n\n# 1. Start the timer
start_time = time.time()

# 2. Run the solver
result = s.check()

# 3. End the timer
end_time = time.time()
elapsed_time = end_time - start_time

if result == sat:
    print("SAT:  Time taken for verification is %.3f s " % elapsed_time)
    m = s.model()
    r = [ m.evaluate(sl_t_win[i]) for i in range(no_of_slices.as_long()) ]
    print("Time windows:")
    print_matrix(r)
    
else:
    print("UNSAT")'''

fp.write(clause)

fp.close()



#===============================================================================
#    Running the Generated SMT-Model to Obtain Time-Cycles
#===============================================================================


result = subprocess.run(["python", "generated_SMT_model.py"], capture_output=True, text=True)

# printing output: time cycles
print("\n --- Output from generated file --- \n")
print(result.stdout)
