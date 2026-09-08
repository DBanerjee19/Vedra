import numpy as np
import pandas as pd
import sys

timesteps = int(sys.argv[1])

def generate_urllc_service(total_timesteps, time_step_ms):
    # fixed independent seed for URLLC behavior
    np.random.seed(202)
    
    timesteps = np.arange(1, total_timesteps + 1)
    time_ms = timesteps * time_step_ms
    
    # traffic arrival
    URLLC_entry = np.random.choice([0, 1], size=total_timesteps, p=[0.75, 0.25])
    
    # radio environment - Relies on robust sub-6GHz channels (Mean SINR = 20 dB)
    sinr_db = np.random.normal(loc=20, scale=2, size=total_timesteps)
    cqi = np.clip((sinr_db / 2).astype(int), 1, 15)
    
    # 5G Physical Layer - Single Stream (SISO) to eradicate multi-antenna jitter
    bandwidth_mhz = 40 # Narrow channel slice for maximum reliability
    snr_linear = 10 ** (sinr_db / 10)
    mimo_layers = 1     
    physical_capacity = bandwidth_mhz * np.log2(1 + snr_linear) * mimo_layers * 0.40
    
    # process throughput
    throughput_mbps = []
    for i in range(total_timesteps):
        if URLLC_entry[i] == 1:
            # low throughput profile to prioritize error resilience (floor around 30 Mbps)
            allocated = max(30.0, physical_capacity[i])
            throughput_mbps.append(round(allocated, 2))
        else:
            throughput_mbps.append(0.0)
            
    df_urllc = pd.DataFrame({
        'Timestep': timesteps,
        'Time_ms': time_ms,
        'URLLC_entry': URLLC_entry,
        'URLLC_5QI': [8 for _ in timesteps], 
        'SINR_dB': np.round(sinr_db, 2),
        'CQI_Index': cqi,
        'Throughput_Mbps': throughput_mbps
    })
    
    return df_urllc, URLLC_entry


# run the URLLC Data Generator
df_urllc, URLLC_entry = generate_urllc_service(timesteps, 5)

# print to output file
with open("URLLC_userdata.txt", "w") as f:
    print(f"{URLLC_entry[:timesteps].tolist()}", file=f)

