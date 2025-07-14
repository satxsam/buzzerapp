#!/usr/bin/env python3
"""
Network setup script for Quiz Buzzer
Finds your IP address and updates the HTML files for network access
"""

import socket
import re
import os

def get_local_ip():
    """Get the local IP address"""
    try:
        # Connect to a remote server to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None

def update_html_files(ip_address):
    """Update HTML files with the correct IP address"""
    files_to_update = ['index.html', 'admin.html']
    
    for filename in files_to_update:
        if not os.path.exists(filename):
            print(f"Warning: {filename} not found")
            continue
            
        # Read the file
        with open(filename, 'r') as f:
            content = f.read()
        
        # Replace localhost with IP address
        updated_content = re.sub(
            r"const wsUrl = 'ws://localhost:8765';",
            f"const wsUrl = 'ws://{ip_address}:8765';",
            content
        )
        
        # Write back to file
        with open(filename, 'w') as f:
            f.write(updated_content)
        
        print(f"✓ Updated {filename}")

def main():
    print("Quiz Buzzer Network Setup")
    print("=" * 30)
    
    # Get IP address
    ip_address = get_local_ip()
    
    if not ip_address:
        print("❌ Could not determine IP address")
        print("\nManual setup required:")
        print("1. Find your IP address:")
        print("   - Windows: ipconfig")
        print("   - Mac/Linux: ifconfig")
        print("2. Edit index.html and admin.html")
        print("3. Change 'ws://localhost:8765' to 'ws://YOUR_IP:8765'")
        return
    
    print(f"📡 Your IP address: {ip_address}")
    print(f"🌐 Server will be accessible at: ws://{ip_address}:8765")
    
    # Ask user if they want to update files
    response = input(f"\nUpdate HTML files to use {ip_address}? (y/n): ").lower().strip()
    
    if response == 'y' or response == 'yes':
        update_html_files(ip_address)
        print("\n✅ Setup complete!")
        print("\nNext steps:")
        print("1. Start the server: python server.py")
        print(f"2. Connect devices to: http://{ip_address}:8000/index.html")
        print(f"3. Admin interface: http://{ip_address}:8000/admin.html")
        print("\nNote: You'll need a simple HTTP server to serve the HTML files.")
        print("Run: python -m http.server 8000")
    else:
        print(f"\nManual setup instructions:")
        print(f"1. Edit index.html and admin.html")
        print(f"2. Change 'ws://localhost:8765' to 'ws://{ip_address}:8765'")
        print(f"3. Start server: python server.py")
        print(f"4. Serve files: python -m http.server 8000")

if __name__ == "__main__":
    main()