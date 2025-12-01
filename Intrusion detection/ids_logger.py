"""
IDS LOGGER
Runs the CIDS algorithm on REAL traffic and saves data to 'cids_log.csv'.
"""
import time
import csv
import can
from bus_config import get_bus

# PAPER PARAMETERS
BATCH_SIZE = 20     
LAMBDA = 0.9995     

class CIDS_Detector:
    def __init__(self):
        self.P = 100.0      
        self.S = 0.0        
        self.O_acc = 0.0    
        self.timestamps = []
        self.start_time = None

    def rls_update(self, t, error):
        G = (self.P * t) / (LAMBDA + t * self.P * t)
        self.P = (self.P - G * t * self.P) / LAMBDA
        self.S = self.S + (G * error)

    def process_batch(self, batch_times):
        N = len(batch_times)
        if N < 2: return 0.0, 0.0
        
        # Initialize start time reference
        if self.start_time is None:
            self.start_time = self.timestamps[0]

        # Calculate Average Interval
        intervals = [batch_times[i] - batch_times[i-1] for i in range(1, N)]
        mu_T = sum(intervals) / len(intervals)
        
        # Calculate Batch Offset
        offsets = []
        t0 = batch_times[0]
        for i in range(1, N):
            expected = t0 + (i * mu_T)
            actual = batch_times[i]
            offsets.append(actual - expected)
        
        avg_offset = sum(offsets) / len(offsets)
        self.O_acc += abs(avg_offset)
        
        # Identification Error
        t_k = batch_times[-1] - self.start_time
        error = self.O_acc - (self.S * t_k)
        
        # Update Model
        self.rls_update(t_k, error)
        
        return self.O_acc, t_k

def run_logger():
    bus = get_bus()
    ids = CIDS_Detector()
    print("💾 IDS Logger Active. Saving to 'cids_log.csv'...")
    
    # Open CSV file
    with open('cids_log.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Time_Sec", "Accumulated_Offset_ms"]) # Header
        
        batch_buffer = []
        
        for msg in bus:
            if msg.arbitration_id == 0x11:
                now = time.time()
                if not ids.timestamps: ids.timestamps.append(now)
                batch_buffer.append(now)
                
                if len(batch_buffer) >= BATCH_SIZE:
                    O_acc, t_k = ids.process_batch(batch_buffer)
                    
                    # Log to file (Convert O_acc to ms)
                    writer.writerow([f"{t_k:.4f}", f"{O_acc * 1000:.4f}"])
                    f.flush() # Ensure data is written immediately
                    
                    print(f"   Logged: Time={t_k:.2f}s | Offset={O_acc*1000:.2f}ms")
                    batch_buffer = []

if __name__ == "__main__":
    run_logger()