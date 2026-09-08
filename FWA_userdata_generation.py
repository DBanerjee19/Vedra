import numpy as np
import pandas as pd

import sys

timesteps = int(sys.argv[1])

def generate_fwa_service(total_timesteps, time_step_ms):
    # fixed independent seed for FWA behavior
    np.random.seed(101)
    
    timesteps = np.arange(1, total_timesteps + 1)
    time_ms = timesteps * time_step_ms
    
    # traffic Arrival - scaled up user count (35% probability)
    FWA_entry = np.random.choice([0, 1], size=total_timesteps, p=[0.65, 0.35])
    
    # radio environment - moderately stable urban signal (Mean SINR = 18 dB)
    sinr_db = np.random.normal(loc=18, scale=4, size=total_timesteps)
    cqi = np.clip((sinr_db / 2).astype(int), 1, 15)
    
    # 5G Physical Layer - standard 2x2 MIMO antennas
    bandwidth_mhz = 100 
    snr_linear = 10 ** (sinr_db / 10)
    mimo_layers = 2     
    physical_capacity = bandwidth_mhz * np.log2(1 + snr_linear) * mimo_layers * 0.55
    
    # process throughput
    throughput_mbps = []
    for i in range(total_timesteps):
        if FWA_entry[i] == 1:
            # FWA baseline expectation (targeting a floor around 220 Mbps)
            allocated = max(220.0, physical_capacity[i])
            throughput_mbps.append(round(allocated, 2))
        else:
            throughput_mbps.append(0.0)
            
    df_fwa = pd.DataFrame({
        'Timestep': timesteps,
        'Time_ms': time_ms,
        'FWA_entry': FWA_entry,
        'FWA_5QI': [6 for _ in timesteps],
        'SINR_dB': np.round(sinr_db, 2),
        'CQI_Index': cqi,
        'Throughput_Mbps': throughput_mbps
    })
    
    return df_fwa, FWA_entry


# run the FWA Data Generator
df_fwa, FWA_entry = generate_fwa_service(timesteps, 5)

# print to output file
with open("FWA_userdata.txt", "w") as f:
    print(f"{FWA_entry[:timesteps].tolist()}", file=f)

