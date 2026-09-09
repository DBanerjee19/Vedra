# VDERA

VEDRA is a *verified* and *efficient* dynamic resource allocation framework for real-time *radio access network* (RAN) scheduling. It deals with one of the key aspects of RAN resource scheduling: allocating *physical resource blocks* (PRBs)—the fundamental units of radio resources—among competing services. 

VEDRA considers any *3-layered network configuration* (Layer1: slices, Layer2: partitions, Layer 3: residual partition) as input, and operates in *two* phases: 
i) a polynomial-time *runtime phase* allocating PRBs to slices within strict *deadlines* (outputs time cycles), and 
ii) a *pre-processing formal verification phase* that guarantees the *dependability* of the proposed allocation before its runtime deployment (outputs runtime allocations).


Reference paper: VEDRA: Verified and Efficient Dynamic Resource Allocation for Real-Time Radio Access Network Scheduling, IEEE Embedded Systems Letters (ESL) 2026 (accepted at workshop Time-Centric Reactive Software (TCRS) 2026)


## Required Software Packages

* SMT solver: [Z3(Microsoft)](https://www.microsoft.com/en-us/research/project/z3-3/)  (used with Python API)

* Packages `numpy`, `json` and `pandas` in Python


## Running the Codebase

We provide all our input networks here: `testcases`. 

The scripts  `execute_preprocessing_verification.py` and `execute_runtime_allocations.py` are available under the `scripts` directory. The first script runs the preprocessing verification phase simulation and the second script runs the runtime allocation phase simulation.  These need to be run with the following command:

* `python execute_preprocessing_verification.py <name_of_the_network>`

* `python execute_runtime_allocations.py <name_of_the_network>`

e.g., run for network1 as follows: `python execute_runtime_allocations.py network1.txt`, and `python execute_runtime_allocations.py network1.txt`


The script `execute_preprocessing_verification.py` automatically:

* generates a wrapper file  (`generate_SMT_model_preprocessing_step.py` under the `src` directory), that generates an SMT-model (`generated_SMT_model.py`) for any 3-layered input network

* runs the generated SMT-model for verification

* the constraints being satisfiable, the synthesized time-cycles are written as inputs in the network input files under `testcases` directory (these are inputs to the runtime allocation phase)

The script `execute_runtime_allocations.py` the automatically:

* generates synthetic service data corresponding to eMBB (Premium and Normal services), URLLC, FWA, mMTC services based on channel quality indicator, MIMO and other inputs (by running the file `eMBB_Premium_userdata_generation.py`, `eMBB_Normal_userdata_generation.py`, `FWA_userdata_generation.py`, `URLLC_userdata_generation.py`, `mMTC_userdata_generation.py` under the `src` directory)

* generates runtime PRB allocaions and de-allocations based on the synthesized time-cycles (by running the file `runtime_allocations.py` under the `src` directory)


Sequentially running `execute_preprocessing_verification.py` and `execute_runtime_allocations.py` generates PRB allocations for all input networks.

## Contributors

* Debarpita Banerjee
* Sumana Ghosh
* Snigdha Das
* Shilpa Budhkar
* Rana Pratap Sircar
