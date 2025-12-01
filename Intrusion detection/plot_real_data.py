import pandas as pd
import matplotlib.pyplot as plt

def plot_log():
    try:
        # Load the data
        print("📖 Reading 'cids_log.csv'...")
        data = pd.read_csv('cids_log.csv')
        
        # Check if empty
        if data.empty:
            print("❌ Error: The log file is empty. Run the simulation longer!")
            return

        # Plot
        plt.figure(figsize=(10, 6))
        plt.plot(data['Time_Sec'], data['Accumulated_Offset_ms'], 
                 label='Measured ID 0x11', color='blue', linewidth=2)
        
        plt.title('Real CIDS Fingerprint (From Simulation)')
        plt.xlabel('Time [Sec]')
        plt.ylabel('Accumulated Clock Offset [ms]')
        plt.legend()
        plt.grid(True)
        
        # Save
        plt.savefig('real_simulation_plot.png')
        print("✅ Plot saved to 'real_simulation_plot.png'")
        
        # Show (if you have a display)
        # plt.show()

    except FileNotFoundError:
        print("❌ Error: 'cids_log.csv' not found. Run ids_logger.py first!")

if __name__ == "__main__":
    plot_log()