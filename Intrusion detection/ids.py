"""
CIDS (Clock-based IDS) - Section 4.1 Implementation
Uses RLS (Recursive Least Squares) to model the arrival time.
Detects Fabrication Attacks by monitoring 'Identification Error'.
"""
import time
import can
from lab_config import get_bus

# PAPER PARAMETERS (Section 5)
BATCH_SIZE = 20     # N in the paper
LAMBDA = 0.9995     # Forgetting factor
THRESHOLD = 5.0     # CUSUM Threshold (Gamma)

class CIDS_Detector:
    def __init__(self):
        self.P = 100.0      # Covariance
        self.S = 0.0        # Skew (Slope)
        self.O_acc = 0.0    # Accumulated Offset
        self.timestamps = []
        
        # CUSUM Variables
        self.mu_e = 0.0     # Mean of error
        self.sigma_e = 0.005  # Variance of error
        self.L_plus = 0.0   # Upper Control Limit

    def rls_update(self, t, error):
        """Executes RLS update for Skew (S) and Covariance (P)"""
        # Algorithm 1, Lines 3-5
        G = (self.P * t) / (LAMBDA + t * self.P * t)
        self.P = (self.P - G * t * self.P) / LAMBDA
        self.S = self.S + (G * error)

    def process_batch(self, batch_times):
        """Calculates Offset and Error for a batch of N messages"""
        N = len(batch_times)
        if N < 2: return
        
        # 1. Calculate Average Interval (mu_T) for this batch
        intervals = [batch_times[i] - batch_times[i-1] for i in range(1, N)]
        mu_T = sum(intervals) / len(intervals)
        
        # 2. Calculate Batch Offset (O_k)
        # Deviation from expected arrival times
        offsets = []
        t0 = batch_times[0]
        for i in range(1, N):
            expected = t0 + (i * mu_T)
            actual = batch_times[i]
            offsets.append(actual - expected)
        
        avg_offset = sum(offsets) / len(offsets)
        
        # 3. Update Accumulated Offset (O_acc)
        # Fabrication Attack causes this to spike POSITIVELY
        self.O_acc += abs(avg_offset)
        
        # 4. Calculate Identification Error (e)
        # t_k is time elapsed since start
        t_k = batch_times[-1] - self.timestamps[0]
        error = self.O_acc - (self.S * t_k)
        
        # 5. Update Model (RLS)
        self.rls_update(t_k, error)
        
        return self.O_acc, error

    def check_cusum(self, error):
        """
        CUSUM Logic (Equation 4 in Paper)
        Detects sudden positive shifts in error.
        """
        # Normalize error
        normalized = (error - self.mu_e) / self.sigma_e
        
        # Update L+ (Upper Control Limit)
        # We subtract 0.5 (k parameter) as standard practice
        self.L_plus = max(0, self.L_plus + normalized - 0.5)
        
        return self.L_plus

def run_cids():
    bus = get_bus()
    ids = CIDS_Detector()
    print("🛡️  CIDS Active. Monitoring ID 0x11...")
    
    batch_buffer = []
    
    for msg in bus:
        if msg.arbitration_id == 0x11:
            now = time.time()
            
            # Initialize start time on first message
            if not ids.timestamps:
                ids.timestamps.append(now)
            
            batch_buffer.append(now)
            
            # Process every N messages
            if len(batch_buffer) >= BATCH_SIZE:
                O_acc, error = ids.process_batch(batch_buffer)
                L_plus = ids.check_cusum(error)
                
                print(f"📊 O_acc: {O_acc:.4f} | Error: {error:.4f} | CUSUM L+: {L_plus:.2f}")
                
                # DETECTION LOGIC
                if L_plus > THRESHOLD:
                    print("   🚨 INTRUSION DETECTED! (Fabrication Attack)")
                    print("   (Sudden positive shift in Accumulated Offset)")
                
                # Keep buffer moving
                batch_buffer = []

if __name__ == "__main__":
    run_cids()