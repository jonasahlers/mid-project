"""
CIDS (Clock-based IDS) - Updated for Masquerade Detection
Implements both L+ and L- (Upper and Lower Control Limits).
Reference: Section 4.2, Equation (4)
"""
import time
import can
from bus_config import get_bus

# PAPER PARAMETERS
BATCH_SIZE = 20     
LAMBDA = 0.9995     
THRESHOLD = 5.0     
K_PARAM = 0.5       # The 'drain' parameter (kappa)

class CIDS_Detector:
    def __init__(self):
        self.P = 100.0      # Covariance
        self.S = 0.0        # Skew (Slope)
        self.O_acc = 0.0    # Accumulated Offset
        self.timestamps = []
        
        # CUSUM Variables
        self.mu_e = 0.0     
        self.sigma_e = 0.005 
        
        self.L_plus = 0.0   # Upper Control Limit (Positive shifts)
        self.L_minus = 0.0  # Lower Control Limit (Negative shifts)

    def rls_update(self, t, error):
        """Executes RLS update for Skew (S) and Covariance (P)"""
        G = (self.P * t) / (LAMBDA + t * self.P * t)
        self.P = (self.P - G * t * self.P) / LAMBDA
        self.S = self.S + (G * error)

    def process_batch(self, batch_times):
        N = len(batch_times)
        if N < 2: return 0.0, 0.0
        
        # 1. Calculate Average Interval
        intervals = [batch_times[i] - batch_times[i-1] for i in range(1, N)]
        mu_T = sum(intervals) / len(intervals)
        
        # 2. Calculate Batch Offset
        offsets = []
        t0 = batch_times[0]
        for i in range(1, N):
            expected = t0 + (i * mu_T)
            actual = batch_times[i]
            offsets.append(actual - expected)
        
        avg_offset = sum(offsets) / len(offsets)
        
        # 3. Accumulated Offset
        self.O_acc += abs(avg_offset)
        
        # 4. Identification Error
        t_k = batch_times[-1] - self.timestamps[0]
        error = self.O_acc - (self.S * t_k)
        
        # 5. Update Model
        self.rls_update(t_k, error)
        
        return self.O_acc, error

    def check_cusum(self, error):
        """
        CUSUM Logic (Equation 4 in Paper)
        Checks both L+ (Positive Shift) and L- (Negative Shift)
        """
        normalized = (error - self.mu_e) / self.sigma_e
        
        # Update L+ (Detects if Error shoots UP)
        self.L_plus = max(0, self.L_plus + normalized - K_PARAM)
        
        # Update L- (Detects if Error shoots DOWN - Common in Masquerade)
        # Note: We subtract normalized error here.
        self.L_minus = max(0, self.L_minus - normalized - K_PARAM)
        
        return self.L_plus, self.L_minus

def run_cids():
    bus = get_bus()
    ids = CIDS_Detector()
    print("🛡️  CIDS Active. Monitoring ID 0x11 (L+ and L-)...")
    
    batch_buffer = []
    
    for msg in bus:
        if msg.arbitration_id == 0x11:
            now = time.time()
            if not ids.timestamps: ids.timestamps.append(now)
            batch_buffer.append(now)
            
            if len(batch_buffer) >= BATCH_SIZE:
                O_acc, error = ids.process_batch(batch_buffer)
                
                # Get both Limits
                L_plus, L_minus = ids.check_cusum(error)
                
                # Print output
                status = f"L+: {L_plus:.2f} | L-: {L_minus:.2f}"
                print(f"📊 O_acc: {O_acc:.4f} | Error: {error:.4f} | {status}")
                
                # DETECTION LOGIC
                if L_plus > THRESHOLD:
                    print("   🚨 INTRUSION DETECTED (Positive Shift - Likely Fabrication)")
                elif L_minus > THRESHOLD:
                    print("   🚨 INTRUSION DETECTED (Negative Shift - Likely Masquerade)")
                
                batch_buffer = []

if __name__ == "__main__":
    run_cids()