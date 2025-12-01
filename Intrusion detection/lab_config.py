import can

# We MUST use udp_multicast for communication between different terminals.
# 'virtual' only works if everything is in one script.
BUS_CONFIG = {
    'interface': 'udp_multicast',
    'channel': '239.255.1.1',
}

def get_bus():
    print(f"🔌 Connecting to bus: {BUS_CONFIG['interface']}...")
    return can.Bus(**BUS_CONFIG)