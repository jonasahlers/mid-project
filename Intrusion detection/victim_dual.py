"""
VICTIM DUAL NODE
Sends TWO messages (0x11 and 0x12) from the same physical clock.
This establishes the correlation baseline for Pairwise Detection.
"""
import time
import can
from bus_config import get_bus

def run_victim_dual():
    bus = get_bus()
    print("😇 Victim (Dual) Active.")
    print("   Sending ID 0x11 (50ms) and ID 0x12 (50ms)...")
    
    next_time_11 = time.time()
    next_time_12 = time.time()
    interval = 0.05

    while True:
        now = time.time()
        
        # Send Message 1 (0x11)
        if now >= next_time_11:
            msg = can.Message(arbitration_id=0x11, data=b'\xAA\x11', is_extended_id=False)
            bus.send(msg)
            next_time_11 += interval

        # Send Message 2 (0x12) - SAME CLOCK SOURCE
        if now >= next_time_12:
            msg = can.Message(arbitration_id=0x12, data=b'\xBB\x22', is_extended_id=False)
            bus.send(msg)
            next_time_12 += interval
        
        # Small sleep to prevent CPU hogging
        time.sleep(0.001)

if __name__ == "__main__":
    run_victim_dual()