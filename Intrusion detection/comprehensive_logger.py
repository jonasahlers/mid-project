"""
COMPREHENSIVE LOGGER
Logs all CIDS metrics (Offset, Error, CUSUM Limits) to CSV.
Use this to generate data for Chapter 5 plots.
"""
import time
import csv
import can
from bus_config import get_bus

# CIDS PARAMETERS
BATCH_SIZE = 20     
LAMBDA = 0.9995     
K_PARAM = 0.5       

class CIDS_Detector:
    def __init__(self):
        # RLS State
        self.P = 100.0      
        self.S = 0.0        
        self.O_acc = 0.0    
        self.timestamps = []
        self.start_time = None
        
        # CUSUM State
        self.mu_e = 0.0     
        self.sigma_e = 0.005 
        self.L_plus = 0.0   
        self.L_minus = 0.0  

    def rls_update(self, t, error):
        G = (self.P * t) / (LAMBDA + t * self.P * t)
        self.P = (self.P - G * t * self.P) / LAMBDA
        self.S = self.S + (G * error)

    def process_batch(self, batch_times):
        N = len(batch_times)
        if N < 2: return None
        
        if self.start_time is None:
            self.start_time = self.timestamps[0]

        # 1. Average Interval & Batch Offset
        intervals = [batch_times[i] - batch_times[i-1] for i in range(1, N)]
        mu_T = sum(intervals) / len(intervals)
        
        offsets = []
        t0 = batch_times[0]
        for i in range(1, N):
            expected = t0 + (i * mu_T)
            actual = batch_times[i]
            offsets.append(actual - expected)
        
        avg_offset = sum(offsets) / len(offsets)
        self.O_acc += abs(avg_offset)
        
        # 2. Identification Error
        t_k = batch_times[-1] - self.start_time
        error = self.O_acc - (self.S * t_k)
        
        # 3. RLS Update
        self.rls_update(t_k, error)
        
        # 4. CUSUM Update
        normalized = (error - self.mu_e) / self.sigma_e
        self.L_plus = max(0, self.L_plus + normalized - K_PARAM)
        self.L_minus = max(0, self.L_minus - normalized - K_PARAM)
        
        return {
            "time": t_k,
            "offset": self.O_acc * 1000, # Convert to ms
            "error": error * 1000,       # Convert to ms (for readability)
            "l_plus": self.L_plus,
            "l_minus": self.L_minus
        }

def run_comprehensive_logger():
    bus = get_bus()
    ids = CIDS_Detector()
    filename = 'cids_full_log.csv'
    
    print(f"📊 Comprehensive Logger Active. Saving to '{filename}'...")
    print("   Waiting for ID 0x11...")
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        # Header matching the paper's plots
        writer.writerow(["Time_Sec", "Accumulated_Offset_ms", "Ident_Error_e", "L_Plus", "L_Minus"])
        
        batch_buffer = []
        
        try:
            for msg in bus:
                if msg.arbitration_id == 0x11:
                    now = time.time()
                    if not ids.timestamps: ids.timestamps.append(now)
                    batch_buffer.append(now)
                    
                    if len(batch_buffer) >= BATCH_SIZE:
                        data = ids.process_batch(batch_buffer)
                        
                        if data:
                            writer.writerow([
                                f"{data['time']:.4f}",
                                f"{data['offset']:.4f}",
                                f"{data['error']:.4f}",
                                f"{data['l_plus']:.4f}",
                                f"{data['l_minus']:.4f}"
                            ])
                            f.flush()
                            print(f"   Logged T={data['time']:.2f}s | L+={data['l_plus']:.2f} | L-={data['l_minus']:.2f}")
                        
                        batch_buffer = []
        except KeyboardInterrupt:
            print("\n💾 Log saved.")

if __name__ == "__main__":
    run_comprehensive_logger()