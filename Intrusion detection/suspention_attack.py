"""
SUSPENSION ATTACK SIMULATION
Simulates a 'Weak Attacker' (Section 3.1) that stops transmitting.
Reference: Section 3.2, Suspension Attack
"""
import time
import can
from bus_config import get_bus

TARGET_ID = 0x11
INTERVAL = 0.05
ALIVE_TIME = 10  # Seconds before the ECU "crashes"/stops

def run_suspension():
    bus = get_bus()
    print(f"💀 Suspension Attack Script Active.")
    print(f"   [0-{ALIVE_TIME}s] transmitting normally...")
    print(f"   [>{ALIVE_TIME}s]  STOPPING transmission (Silence).")
    
    start_time = time.time()
    next_time = start_time

    while True:
        now = time.time()
        
        # Check if we should die
        if (now - start_time) > ALIVE_TIME:
            print("   ❌ SUSPENDED. Stopping transmission now.")
            break 
            
        if now >= next_time:
            msg = can.Message(arbitration_id=TARGET_ID, data=b'\xDE\xAD', is_extended_id=False)
            bus.send(msg)
            next_time += INTERVAL
        
        time.sleep(0.001)

if __name__ == "__main__":
    run_suspension()