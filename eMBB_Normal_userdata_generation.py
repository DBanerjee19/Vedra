import numpy as np
import pandas as pd
import sys  


timesteps = int(sys.argv[1])

def generate_embb_normal_service(total_timesteps, time_step_ms):
    # fixed independent seed for Normal user behavior
    np.random.seed(99)
    
    timesteps = np.arange(1, total_timesteps + 1)
    time_ms = timesteps * time_step_ms
    
    # traffic arrival - denser congestion for Normal users (80% probability)
    Normal_entry = np.random.choice([0, 1], size=total_timesteps, p=[0.2, 0.8])
    
    # radio Environment - standard, more interfered signal (Mean SINR = 15 dB)
    sinr_db = np.random.normal(loc=15, scale=5, size=total_timesteps)
    cqi = np.clip((sinr_db / 2).astype(int), 1, 15)
    
    # 5G Physical Layer - 100MHz bandwidth with baseline 2x2 MIMO layers
    bandwidth_mhz = 100 
    snr_linear = 10 ** (sinr_db / 10)
    mimo_layers = 2     
    physical_capacity = bandwidth_mhz * np.log2(1 + snr_linear) * mimo_layers * 0.55
    
    # process throughput
    throughput_mbps = []
    for i in range(total_timesteps):
        if Normal_entry[i] == 1:
            # enforce 5QI 9 baseline target requirements (120 Mbps)
            allocated = max(120.0, physical_capacity[i])
            throughput_mbps.append(round(allocated, 2))
        else:
            throughput_mbps.append(0.0)
            
    df_normal = pd.DataFrame({
        'Timestep': timesteps,
        'Time_ms': time_ms,
        'Normal_entry': Normal_entry,
        'Normal_5QI': [9 for _ in timesteps],
        'SINR_dB': np.round(sinr_db, 2),
        'CQI_Index': cqi,
        'Throughput_Mbps': throughput_mbps
    })
    
    return df_normal, Normal_entry


# run the Normal Data Generator
df_normal, Normal_entry = generate_embb_normal_service(timesteps, 5)

# print to output file
with open("eMBB_Normal_userdata.txt", "w") as f:
    print(f"{Normal_entry[:timesteps].tolist()}", file=f)

