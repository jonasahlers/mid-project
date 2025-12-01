"""
MASQUERADE ATTACK SIMULATION
Implements the scenario in Section 3.2 (Figure 2c) of the paper.

1. Victim sends ID 0x11 for 10 seconds.
2. Victim stops.
3. Attacker starts sending ID 0x11 immediately.
   CRITICAL: Attacker runs slightly FASTER (0.5% skew) to simulate 
   a different physical clock crystal.
"""
import time
import can
from bus_config import get_bus

# CONFIGURATION
# The ID we are spoofing
TARGET_ID = 0x11
# How often the legitimate ECU sends (50ms)
NORMAL_INTERVAL = 0.05 
# The moment the attack happens (seconds)
T_MASQ = 10 
# The Attacker's "Clock Skew". 
# 0.995 means the attacker is 0.5% faster than the victim.
# In real hardware, this difference is inherent to the crystal oscillator.
SKEW_FACTOR = 0.995 

def run_simulation():
    bus = get_bus()
    start_time = time.time()
    
    print(f"🎭 Masquerade Script Active.")
    print(f"   [0-{T_MASQ}s] Victim transmitting ID {hex(TARGET_ID)}...")
    print(f"   [>{T_MASQ}s]  Attacker takes over (with {SKEW_FACTOR}x skew).")

    # We use a loop to control the timeline preciseley
    msg_count = 0
    
    try:
        while True:
            now = time.time()
            elapsed = now - start_time
            
            # --- PHASE 1: VICTIM (Legitimate) ---
            if elapsed < T_MASQ:
                # Send legitimate message
                msg = can.Message(arbitration_id=TARGET_ID, data=b'\xAA\xBB', is_extended_id=False)
                bus.send(msg)
                
                # Sleep exactly the normal interval
                time.sleep(NORMAL_INTERVAL)
                
            # --- PHASE 2: ATTACKER (Masquerade) ---
            else:
                if msg_count == 0:
                    print("\n🔥 MASQUERADE HANDOVER! Victim stopped. Attacker started.")
                    print("   (Frequency is the same, but Clock Skew is different!)")
                    msg_count += 1
                
                # Send spoofed message
                msg = can.Message(arbitration_id=TARGET_ID, data=b'\xDE\xAD', is_extended_id=False)
                bus.send(msg)
                
                # CRITICAL: We sleep slightly LESS to simulate a faster clock.
                # This changes the slope of the Accumulated Offset in the IDS.
                time.sleep(NORMAL_INTERVAL * SKEW_FACTOR)

    except KeyboardInterrupt:
        print("🛑 Simulation stopped.")

if __name__ == "__main__":
    run_simulation()