"""
CIDS FAST SIMULATION V2 (FIXED ALGORITHM)
-----------------------------------------
Fixes the 'offset masking' bug by using the Previous Batch's 
interval to calculate the Current Batch's offset (Paper Algorithm 1).
"""

import matplotlib.pyplot as plt
import pandas as pd
import random

# --- CONFIGURATION ---
TARGET_ID = 0x11
BATCH_SIZE = 20
LAMBDA = 0.9995
K_PARAM = 0.5
THRESHOLD = 5.0

class CIDS_Detector:
    def __init__(self):
        self.P = 100.0      
        self.S = 0.0        
        self.O_acc = 0.0    
        self.timestamps = []
        self.start_time = None
        
        # CUSUM
        self.mu_e = 0.0     
        self.sigma_e = 0.005 
        self.L_plus = 0.0   
        self.L_minus = 0.0  
        
        # CRITICAL: Store the PREVIOUS batch's average interval
        self.prev_mu_T = None 
        
        self.log_data = []

    def rls_update(self, t, error):
        G = (self.P * t) / (LAMBDA + t * self.P * t)
        self.P = (self.P - G * t * self.P) / LAMBDA
        self.S = self.S + (G * error)

    def process_batch(self, batch_times):
        N = len(batch_times)
        if N < 2: return

        if self.start_time is None:
            self.start_time = self.timestamps[0]

        # 1. Calculate Current Batch Average Interval (mu_T_k)
        intervals = [batch_times[i] - batch_times[i-1] for i in range(1, N)]
        current_mu_T = sum(intervals) / len(intervals)
        
        # 2. Calculate Offset (O_k)
        # CRITICAL FIX: Use PREVIOUS mu_T to calculate offsets for CURRENT batch.
        # If we use current_mu_T, we hide the skew change!
        reference_mu_T = self.prev_mu_T if self.prev_mu_T else current_mu_T
        
        t0 = batch_times[0]
        # Algorithm 1 Line 22: Expected time based on PREVIOUS interval
        offsets = [(batch_times[i] - (t0 + i * reference_mu_T)) for i in range(1, N)]
        avg_offset = sum(offsets) / len(offsets)
        
        # Update state for next batch
        self.prev_mu_T = current_mu_T
        
        # 3. Accumulated Offset
        # Note: We take absolute value as per CIDS generic logic, 
        # but for Masquerade (skew change), the sign matters for direction.
        # The paper says O_acc = O_acc + |O[k]|.
        self.O_acc += abs(avg_offset)
        
        # 4. Identification Error
        t_k = batch_times[-1] - self.start_time
        error = self.O_acc - (self.S * t_k)
        
        # 5. RLS Update
        self.rls_update(t_k, error)
        
        # 6. CUSUM Update
        normalized = (error - self.mu_e) / self.sigma_e
        self.L_plus = max(0, self.L_plus + normalized - K_PARAM)
        self.L_minus = max(0, self.L_minus - normalized - K_PARAM)
        
        # 7. Log
        self.log_data.append({
            "Time_Sec": t_k,
            "Accumulated_Offset_ms": self.O_acc * 1000,
            "Ident_Error_e": error * 1000,
            "L_Plus": self.L_plus,
            "L_Minus": self.L_minus
        })

# --- SCENARIO RUNNER ---

def run_simulation(scenario_name, duration_base, duration_attack, attack_type):
    print(f"⚡ Simulating {scenario_name}...")
    
    ids = CIDS_Detector()
    current_time = 0.0
    batch_buffer = []
    
    # Lower Jitter for cleaner plots (Real ECUs are stable)
    JITTER_RANGE = 0.00005 # 50 microseconds
    
    # 1. NORMAL PHASE
    while current_time < duration_base:
        jitter = random.uniform(-JITTER_RANGE, JITTER_RANGE)
        interval = 0.05 + jitter
        current_time += interval
        
        if not ids.timestamps: ids.timestamps.append(current_time)
        batch_buffer.append(current_time)
        
        if len(batch_buffer) >= BATCH_SIZE:
            ids.process_batch(batch_buffer)
            batch_buffer = []

    # 2. ATTACK PHASE
    attack_end_time = duration_base + duration_attack
    last_suspension_check = current_time
    
    while current_time < attack_end_time:
        
        if attack_type == "fabrication":
            # Flooding
            interval = 0.002
            current_time += interval
            batch_buffer.append(current_time)
            if len(batch_buffer) >= BATCH_SIZE:
                ids.process_batch(batch_buffer)
                batch_buffer = []

        elif attack_type == "masquerade":
            # Skew Change: 0.1% change is enough to detect if logic is right
            jitter = random.uniform(-JITTER_RANGE, JITTER_RANGE)
            interval = (0.05 * 0.999) + jitter 
            current_time += interval
            
            batch_buffer.append(current_time)
            if len(batch_buffer) >= BATCH_SIZE:
                ids.process_batch(batch_buffer)
                batch_buffer = []

        elif attack_type == "suspension":
            step = 0.1
            current_time += step
            
            if (current_time - last_suspension_check) > 0.5:
                fake_time = current_time
                missing = BATCH_SIZE - len(batch_buffer)
                for _ in range(missing):
                    fake_time += 10.0 
                    batch_buffer.append(fake_time)
                
                ids.process_batch(batch_buffer)
                batch_buffer = [] 
                last_suspension_check = current_time
                
    return pd.DataFrame(ids.log_data)

# --- PLOTTING ---

def plot_results(df, title, filename):
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    
    # Offset
    ax1.plot(df['Time_Sec'], df['Accumulated_Offset_ms'], color='blue', lw=2)
    ax1.set_ylabel(r'$O_{acc}$ [ms]')
    ax1.set_title(title, fontsize=14, fontweight='bold')
    ax1.grid(True)
    
    # Error
    ax2.plot(df['Time_Sec'], df['Ident_Error_e'], color='purple', lw=1)
    ax2.set_ylabel(r'Error $e$')
    ax2.axhline(0, color='black', linestyle='--', lw=0.5)
    ax2.grid(True)
    
    # CUSUM
    ax3.plot(df['Time_Sec'], df['L_Plus'], label='$L^+$', color='red', lw=2)
    ax3.plot(df['Time_Sec'], df['L_Minus'], label='$L^-$', color='green', lw=2, linestyle='--')
    ax3.axhline(THRESHOLD, color='black', linestyle='-.', label='Threshold')
    
    ax3.set_ylabel('CUSUM Limits')
    ax3.set_xlabel('Time [Sec]')
    ax3.legend(loc='upper left')
    ax3.grid(True)
    
    plt.tight_layout()
    plt.savefig(filename)
    print(f"✅ Saved {filename}")
    plt.close()

if __name__ == "__main__":
    # Fabrication
    df1 = run_simulation("Fabrication", 400, 50, "fabrication")
    plot_results(df1, "Fabrication Attack (Flooding)", "fixed_plot_fabrication.png")
    
    # Suspension
    df2 = run_simulation("Suspension", 400, 50, "suspension")
    plot_results(df2, "Suspension Attack (Silence)", "fixed_plot_suspension.png")
    
    # Masquerade (Longer duration to show skew accumulation)
    df3 = run_simulation("Masquerade", 400, 400, "masquerade")
    plot_results(df3, "Masquerade Attack (Skew Change)", "fixed_plot_masquerade.png")