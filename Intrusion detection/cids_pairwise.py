"""
CIDS PAIRWISE DETECTION (Section 5.4)
Correlates the clock offsets of ID 0x11 and ID 0x12.
"""
import time
import can
import math
from bus_config import get_bus

BATCH_SIZE = 20

class SingleTracker:
    def __init__(self):
        self.timestamps = []
    
    def get_batch_offset(self, batch_times):
        """Calculates the average offset for a single batch"""
        N = len(batch_times)
        if N < 2: return 0.0
        
        # Calculate Interval Mean
        intervals = [batch_times[i] - batch_times[i-1] for i in range(1, N)]
        mu_T = sum(intervals) / len(intervals)
        
        # Calculate Offsets relative to first message in batch
        offsets = []
        t0 = batch_times[0]
        for i in range(1, N):
            expected = t0 + (i * mu_T)
            actual = batch_times[i]
            offsets.append(actual - expected)
        
        # Return average offset of this batch
        return sum(offsets) / len(offsets)

def calculate_correlation(list_x, list_y):
    """Pearson Correlation Coefficient"""
    n = len(list_x)
    if n != len(list_y) or n < 2: return 0.0
    
    mean_x = sum(list_x) / n
    mean_y = sum(list_y) / n
    
    numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(list_x, list_y))
    sum_sq_x = sum((xi - mean_x) ** 2 for xi in list_x)
    sum_sq_y = sum((yi - mean_y) ** 2 for yi in list_y)
    
    denominator = math.sqrt(sum_sq_x * sum_sq_y)
    if denominator == 0: return 0.0
    
    return numerator / denominator

def run_pairwise_cids():
    bus = get_bus()
    print("🤝 CIDS Pairwise Detector Active.")
    print("   Monitoring Correlation between 0x11 and 0x12...")

    trackers = {0x11: SingleTracker(), 0x12: SingleTracker()}
    buffers = {0x11: [], 0x12: []}
    
    # History of Average Offsets for Correlation
    history_offsets = {0x11: [], 0x12: []}
    
    for msg in bus:
        mid = msg.arbitration_id
        if mid in [0x11, 0x12]:
            now = time.time()
            buffers[mid].append(now)
            
            # Process Batch
            if len(buffers[mid]) >= BATCH_SIZE:
                avg_offset = trackers[mid].get_batch_offset(buffers[mid])
                history_offsets[mid].append(avg_offset)
                buffers[mid] = [] # Reset buffer
                
                # Check Correlation if we have enough history
                len_11 = len(history_offsets[0x11])
                len_12 = len(history_offsets[0x12])
                min_len = min(len_11, len_12)
                
                if min_len >= 5: # Need a few points to correlate
                    # CRITICAL FIX: Slice from the START ([:min_len]), not the end.
                    # This ensures we compare Batch 1 with Batch 1, even if one list is longer.
                    data_11 = history_offsets[0x11][:min_len]
                    data_12 = history_offsets[0x12][:min_len]
                    
                    corr = calculate_correlation(data_11, data_12)
                    
                    print(f"📊 Correlation (0x11 vs 0x12): {corr:.4f}")
                    
                    if corr < 0.2:
                        print("   🚨 PAIRWISE ALARM: Messages are uncorrelated! (Likely Masquerade)")
                    elif corr > 0.8:
                        print("   ✅ Normal: Clocks are synchronized.")

if __name__ == "__main__":
    run_pairwise_cids()