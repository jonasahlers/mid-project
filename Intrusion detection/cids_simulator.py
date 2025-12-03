"""
CIDS FIGURE 6/7 REPLICATION (DUAL PLOT + EXTENDED TIME)
-------------------------------------------------------
Simulates 'Attack' vs 'No Attack' simultaneously to match
Figures 6 and 7 in the Cho & Shin (2016) paper.
"""

import matplotlib.pyplot as plt
import pandas as pd
import random

# --- CONFIGURATION ---
BATCH_SIZE = 20
LAMBDA = 0.9995
K_PARAM = 0.5
THRESHOLD = 5.0
# Matches Paper Figure 6: Total 800s, Attack at 400s
DURATION_TOTAL = 800 
ATTACK_START_TIME = 400

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
        
        # Previous Batch Interval (Paper Algorithm 1 logic)
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

        # 1. Calculate Current Batch Average Interval
        intervals = [batch_times[i] - batch_times[i-1] for i in range(1, N)]
        current_mu_T = sum(intervals) / len(intervals)
        
        # 2. Calculate Offset
        # Use PREVIOUS mu_T to calculate offsets for CURRENT batch (Alg 1)
        reference_mu_T = self.prev_mu_T if self.prev_mu_T else current_mu_T
        
        t0 = batch_times[0]
        offsets = [(batch_times[i] - (t0 + i * reference_mu_T)) for i in range(1, N)]
        avg_offset = sum(offsets) / len(offsets)
        
        # Update state
        self.prev_mu_T = current_mu_T
        
        # 3. Accumulated Offset
        self.O_acc += abs(avg_offset)
        
        # 4. Identification Error
        t_k = batch_times[-1] - self.start_time
        error = self.O_acc - (self.S * t_k)
        
        # 5. RLS Update
        self.rls_update(t_k, error)
        
        # 6. CUSUM Update
        # Paper uses dynamic limits, but simple static sigma works for reproduction
        normalized = (error - self.mu_e) / self.sigma_e
        self.L_plus = max(0, self.L_plus + normalized - K_PARAM)
        self.L_minus = max(0, self.L_minus - normalized - K_PARAM)
        
        self.log_data.append({
            "Time_Sec": t_k,
            "Accumulated_Offset_ms": self.O_acc * 1000,
            "Ident_Error_e": error * 1000,
            "L_Plus": self.L_plus,
            "L_Minus": self.L_minus
        })

# --- DUAL SCENARIO RUNNER ---

def run_dual_simulation(attack_type):
    print(f"⚡ Simulating {attack_type} (With vs Without Attack)...")
    
    # We run TWO detectors simultaneously
    ids_attack = CIDS_Detector() # Will experience the attack
    ids_normal = CIDS_Detector() # Will stay normal (Ghost line)
    
    # Independent time trackers
    time_attack = 0.0
    time_normal = 0.0
    
    batch_buf_attack = []
    batch_buf_normal = []
    
    # Last check for suspension timeout logic
    last_suspension_check = 0.0
    
    JITTER_RANGE = 0.00005 # 50us jitter
    BASE_INTERVAL = 0.05   # 50ms period

    # Loop until the ATTACK timeline finishes
    while time_attack < DURATION_TOTAL:
        
        # --- 1. GENERATE BASE JITTER ---
        # We use the same jitter for both lines before the attack 
        # to ensure they overlap perfectly initially.
        common_jitter = random.uniform(-JITTER_RANGE, JITTER_RANGE)
        
        # --- 2. UPDATE "WITHOUT ATTACK" (NORMAL) LINE ---
        # Always just adds the normal interval
        interval_n = BASE_INTERVAL + common_jitter
        time_normal += interval_n
        
        if not ids_normal.timestamps: ids_normal.timestamps.append(time_normal)
        batch_buf_normal.append(time_normal)
        
        if len(batch_buf_normal) >= BATCH_SIZE:
            ids_normal.process_batch(batch_buf_normal)
            batch_buf_normal = []
            
        # --- 3. UPDATE "WITH ATTACK" LINE ---
        
        # A. Before Attack Start -> Behaves exactly like Normal
        if time_attack < ATTACK_START_TIME:
            interval_a = BASE_INTERVAL + common_jitter
            time_attack += interval_a
            
            if not ids_attack.timestamps: ids_attack.timestamps.append(time_attack)
            batch_buf_attack.append(time_attack)
            
            if len(batch_buf_attack) >= BATCH_SIZE:
                ids_attack.process_batch(batch_buf_attack)
                batch_buf_attack = []
            
            last_suspension_check = time_attack

        # B. After Attack Start -> Apply Attack Logic
        else:
            if attack_type == "fabrication":
                # Fabrication: Inject messages very fast (flooding)
                # Paper Fig 6a: O_acc shoots up because interval drops drastically
                interval_a = 0.002 # 2ms injection
                time_attack += interval_a
                batch_buf_attack.append(time_attack)
                
                if len(batch_buf_attack) >= BATCH_SIZE:
                    ids_attack.process_batch(batch_buf_attack)
                    batch_buf_attack = []

            elif attack_type == "suspension":
                # Suspension: Stop sending.
                # The detector waits... time moves forward artificially for the plot
                step = 0.1
                time_attack += step # Real world time passes
                
                # Logic: If no message for > 0.5s, fill batch with high values (Alg 1)
                if (time_attack - last_suspension_check) > 0.5:
                    fake_time = time_attack
                    missing = BATCH_SIZE - len(batch_buf_attack)
                    # Fill buffer with massive delays to signify "Lost" messages
                    for _ in range(missing):
                        fake_time += 10.0 # Huge interval
                        batch_buf_attack.append(fake_time)
                    
                    ids_attack.process_batch(batch_buf_attack)
                    batch_buf_attack = []
                    last_suspension_check = time_attack

    return pd.DataFrame(ids_attack.log_data), pd.DataFrame(ids_normal.log_data)

# --- PLOTTING (MATCHING PAPER STYLE) ---

def plot_paper_figure(df_attack, df_normal, title, filename):
    # Setup 3 subplots like Figure 6
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    
    # 1. Accumulated Offset (O_acc)
    # Dashed Blue/Black = Without Attack
    ax1.plot(df_normal['Time_Sec'], df_normal['Accumulated_Offset_ms'], 
             color='navy', linestyle='--', alpha=0.7, label='w/o attack')
    # Solid Red = With Attack
    ax1.plot(df_attack['Time_Sec'], df_attack['Accumulated_Offset_ms'], 
             color='crimson', lw=2, label='w/ attack')
    
    ax1.set_ylabel(r'$O_{acc}$ [ms]')
    ax1.set_title(title + r' ($O_{acc}$)', fontsize=12, fontweight='bold')
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)
    
    # 2. Identification Error (e)
    ax2.plot(df_normal['Time_Sec'], df_normal['Ident_Error_e'], 
             color='navy', linestyle='--', alpha=0.3)
    ax2.plot(df_attack['Time_Sec'], df_attack['Ident_Error_e'], 
             color='crimson', lw=1.5)
    
    ax2.set_ylabel(r'Ident Error $e$')
    ax2.axhline(0, color='black', linestyle='--', lw=0.5)
    ax2.grid(True, alpha=0.3)
    
    # 3. Control Limits (L)
    # Paper Figure 6 plots Upper Control Limit (L+) for Fabrication/Suspension
    ax3.plot(df_normal['Time_Sec'], df_normal['L_Plus'], 
             color='navy', linestyle='--', alpha=0.3, label='w/o attack')
    ax3.plot(df_attack['Time_Sec'], df_attack['L_Plus'], 
             color='crimson', lw=2, label='w/ attack')
    
    ax3.axhline(THRESHOLD, color='black', linestyle='-.', label='Threshold')
    
    ax3.set_ylabel(r'Upper Limit $L^+$')
    ax3.set_xlabel('Time [Sec]')
    ax3.legend(loc="upper left")
    ax3.grid(True, alpha=0.3)
    
    # Set X-Axis to match paper (0 to 800)
    plt.xlim(0, DURATION_TOTAL)
    
    plt.tight_layout()
    plt.savefig(filename)
    print(f"✅ Saved {filename}")
    plt.close()

if __name__ == "__main__":
    # 1. Fabrication Attack (Figure 6a)
    df_att, df_norm = run_dual_simulation("fabrication")
    plot_paper_figure(df_att, df_norm, "Fabrication Attack", "figure_6a_replication.png")
    
    # 2. Suspension Attack (Figure 6b)
    df_att, df_norm = run_dual_simulation("suspension")
    plot_paper_figure(df_att, df_norm, "Suspension Attack", "figure_6b_replication.png")