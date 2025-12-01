"""
CHAPTER 5 PLOTTER
Replicates the 3-subplot layout from the paper (Figures 6, 7, 8).
"""
import pandas as pd
import matplotlib.pyplot as plt

def plot_full_results():
    try:
        data = pd.read_csv('cids_full_log.csv')
        if data.empty:
            print("❌ CSV is empty.")
            return

        # Setup Figure with 3 subplots sharing the X-axis
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), sharex=True)
        
        # Subplot 1: Accumulated Clock Offset
        ax1.plot(data['Time_Sec'], data['Accumulated_Offset_ms'], color='blue', linewidth=2)
        ax1.set_ylabel(r'Accum. Clock Offset ($O_{acc}$) [ms]', fontsize=12)
        ax1.set_title('CIDS Intrusion Detection Analysis', fontsize=16)
        ax1.grid(True)

        # Subplot 2: Identification Error
        ax2.plot(data['Time_Sec'], data['Ident_Error_e'], color='purple', linewidth=1.5)
        ax2.set_ylabel(r'Ident. Error ($e$)', fontsize=12)
        ax2.axhline(0, color='black', linestyle='--', linewidth=0.8)
        ax2.grid(True)

        # Subplot 3: Control Limits (L+ and L-)
        ax3.plot(data['Time_Sec'], data['L_Plus'], label='$L^+$ (Fabrication)', color='red', linewidth=2)
        ax3.plot(data['Time_Sec'], data['L_Minus'], label='$L^-$ (Masquerade)', color='green', linewidth=2, linestyle='--')
        
        # Add Threshold Line (Gamma = 5)
        ax3.axhline(5, color='black', linestyle='-.', label='Threshold ($\Gamma_L=5$)')
        
        ax3.set_ylabel('Control Limits ($L$)', fontsize=12)
        ax3.set_xlabel('Time [Sec]', fontsize=14)
        ax3.legend(loc='upper left')
        ax3.grid(True)

        plt.tight_layout()
        plt.savefig('chapter_5_replication.png')
        print("✅ Plot saved to 'chapter_5_replication.png'")
        # plt.show() 

    except FileNotFoundError:
        print("❌ 'cids_full_log.csv' not found.")

if __name__ == "__main__":
    plot_full_results()