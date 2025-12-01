"""
CIDS SUSPENSION DEFENSE (Section 5.2)
Handles the case where messages STOP arriving.
"""
import time
import can
from bus_config import get_bus
from cids import CIDS_Detector, BATCH_SIZE, THRESHOLD

# If we don't see a message for 0.5s (10x normal), assume suspension
TIMEOUT_LIMIT = 0.5 

def run_cids_suspension():
    bus = get_bus()
    ids = CIDS_Detector()
    print("🛡️  CIDS Suspension Detector Active.")
    print(f"   Timeout threshold set to {TIMEOUT_LIMIT}s")
    
    batch_buffer = []
    last_arrival = time.time() # Initialize timer
    
    try:
        while True:
            # NON-BLOCKING RECEIVE
            msg = bus.recv(timeout=0.1)
            now = time.time()
            
            # --- NORMAL MESSAGE PROCESSING ---
            if msg and msg.arbitration_id == 0x11:
                last_arrival = now
                if not ids.timestamps: ids.timestamps.append(now)
                batch_buffer.append(now)
                
                if len(batch_buffer) >= BATCH_SIZE:
                    O_acc, error = ids.process_batch(batch_buffer)
                    L_plus, L_minus = ids.check_cusum(error)
                    print(f"📊 Normal: O_acc={O_acc:.4f} | L+={L_plus:.2f}")
                    batch_buffer = []

            # --- SUSPENSION DETECTION LOGIC ---
            time_since_last = now - last_arrival
            
            if time_since_last > TIMEOUT_LIMIT:
                print(f"   ⚠️  SILENCE DETECTED ({time_since_last:.2f}s)!")
                
                # --- FIX START: Prevent crash if no baseline exists ---
                if not ids.timestamps:
                    print("   ⏳ No baseline established yet. Waiting for victim...")
                    last_arrival = now # Reset timer to avoid spam loop
                    continue
                # --- FIX END ---
                
                # Force fill the batch with "Significantly High Values"
                missing_count = BATCH_SIZE - len(batch_buffer)
                fake_time = now
                for _ in range(missing_count):
                    fake_time += 10.0 
                    batch_buffer.append(fake_time)
                
                # Now it is safe to process because timestamps is not empty
                O_acc, error = ids.process_batch(batch_buffer)
                L_plus, L_minus = ids.check_cusum(error)
                
                print(f"   📉 FORCED BATCH STATS: Error={error:.2f} | L+={L_plus:.2f}")

                if L_plus > THRESHOLD:
                    print("   🚨 INTRUSION DETECTED (Suspension Attack)")
                    batch_buffer = []
                    last_arrival = time.time()
                
                batch_buffer = []

    except KeyboardInterrupt:
        print("Stopped.")

if __name__ == "__main__":
    run_cids_suspension()