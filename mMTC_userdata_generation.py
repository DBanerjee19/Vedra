import numpy as np
import pandas as pd
import sys

timesteps = int(sys.argv[1])


def generate_mmtc_service(total_timesteps, time_step_ms):
    # fixed independent seed for mMTC behavior
    np.random.seed(303)
    
    timesteps = np.arange(1, total_timesteps + 1)
    time_ms = timesteps * time_step_ms
    
    # traffic Arrival - Scaled up user count (20% probability)
    mMTC_entry = np.random.choice([0, 1], size=total_timesteps, p=[0.80, 0.20])
    
    # radio rnvironment - poor signal profiles, simulating deep indoor sensors (Mean SINR = 8 dB)
    sinr_db = np.random.normal(loc=8, scale=6, size=total_timesteps)
    cqi = np.clip((sinr_db / 2).astype(int), 1, 15)
    
    # 5G Physical Layer - narrowband IoT allocation
    bandwidth_mhz = 1.4 
    snr_linear = 10 ** (sinr_db / 10)
    mimo_layers = 1     
    physical_capacity = bandwidth_mhz * np.log2(1 + snr_linear) * mimo_layers * 0.50
    
    # process throughput
    throughput_mbps = []
    for i in range(total_timesteps):
        if mMTC_entry[i] == 1:
            # tiny sensor packet transmission bounds
            allocated = max(0.5, physical_capacity[i])
            throughput_mbps.append(round(allocated, 4))
        else:
            throughput_mbps.append(0.0)
            

    df_mmtc = pd.DataFrame({
        'Timestep': timesteps,
        'Time_ms': time_ms,
        'mMTC_entry': mMTC_entry,
        'mMTC_5QI': [9 for _ in timesteps], 
        'SINR_dB': np.round(sinr_db, 2),
        'CQI_Index': cqi,
        'Throughput_Mbps': throughput_mbps
    })
    
    return df_mmtc, mMTC_entry


# run the mMTC Data Generator
df_mmtc, mMTC_entry = generate_mmtc_service(timesteps, 5)

# print to output file
with open("mMTC_userdata.txt", "w") as f:
    print(f"{mMTC_entry[:timesteps].tolist()}", file=f)
