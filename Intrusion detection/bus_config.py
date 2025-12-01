import can


BUS_CONFIG = {
    'interface': 'udp_multicast',
    'channel': '239.255.1.1',
}

def get_bus():
    print(f"🔌 Connecting to bus: {BUS_CONFIG['interface']}...")
    return can.Bus(**BUS_CONFIG)