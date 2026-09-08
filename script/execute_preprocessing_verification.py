import os
import subprocess

# all input files
network_files = ["network1.txt", "network2.txt", "network3.txt", "network4.txt"]

# runtime_allocation code is in 'src' directory
base_dir = os.path.dirname(os.path.abspath(__file__))
target_script = os.path.abspath(os.path.join(base_dir, "..", "src", "generate_SMT_model_preprocessing_step.py"))


# 3. loop through each input file
for filename in network_files:
    print(f"=========================================")
    print(f"Executing runtime_allocations.py for: {filename}")
    print(f"=========================================")
    
    #run the script using the python command, passing the filename as the second argument
    result = subprocess.run(["python", target_script, filename])
    
    # check if the execution failed
    if result.returncode != 0:
        print(f"Error occurred while processing {filename}\n")
    else:
        print(f"Finished processing {filename}\n")
