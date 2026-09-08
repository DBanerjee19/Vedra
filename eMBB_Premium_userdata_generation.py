import numpy as np
import pandas as pd
import sys

timesteps = int(sys.argv[1])


def generate_embb_premium_service(total_timesteps, time_step_ms):
    # fixed seed for reproducibility
    np.random.seed(42)
    
    timesteps = np.arange(1, total_timesteps + 1)
    time_ms = timesteps * time_step_ms
    
    # traffic arrival - lower density for Premium users (30% probability)
    Pre_entry = np.random.choice([0, 1], size=total_timesteps, p=[0.45, 0.55])
    
    # radio Environment - clean, high-quality signal (Mean SINR = 24 dB)
    sinr_db = np.random.normal(loc=24, scale=3, size=total_timesteps)
    cqi = np.clip((sinr_db / 2).astype(int), 1, 15)
    
    # 5G Physical Layer - 100MHz bandwidth with Premium 4x4 MIMO layers
    bandwidth_mhz = 100 
    snr_linear = 10 ** (sinr_db / 10)
    mimo_layers = 4     
    physical_capacity = bandwidth_mhz * np.log2(1 + snr_linear) * mimo_layers * 0.65
    
    # 4. process throughput
    throughput_mbps = []
    for i in range(total_timesteps):
        if Pre_entry[i] == 1:
            # Enforce 5QI 6 Premium target floor requirement (450 Mbps)
            allocated = max(450.0, physical_capacity[i])
            throughput_mbps.append(round(allocated, 2))
        else:
            throughput_mbps.append(0.0)
            
    df_premium = pd.DataFrame({
        'Timestep': timesteps,
        'Time_ms': time_ms,
        'Pre_entry': Pre_entry,
        'Premium_5QI': [6 for _ in timesteps],
        'SINR_dB': np.round(sinr_db, 2),
        'CQI_Index': cqi,
        'Throughput_Mbps': throughput_mbps
    })
    
    return df_premium, Pre_entry

# run the Premium Data Generator
df_premium, Pre_entry = generate_embb_premium_service(timesteps, 5)


# print to output file
with open("eMBB_Premium_userdata.txt", "w") as f:
    print(f"{Pre_entry[:timesteps].tolist()}", file=f)


