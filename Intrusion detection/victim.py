
import time
import can
from bus_config import get_bus

def run_victim():
    bus = get_bus()
    print("Victim Active. Sending ID 0x11 every 0.05s...")
    
    next_time = time.time()
    interval = 0.05 # 50ms

    while True:
        now = time.time()
        if now >= next_time:
            msg = can.Message(arbitration_id=0x11, data=b'\xAA\xBB', is_extended_id=False)
            bus.send(msg)
            
            
            next_time += interval
        
        time.sleep(0.001)

if __name__ == "__main__":
    run_victim()