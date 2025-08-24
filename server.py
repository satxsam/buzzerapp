#!/usr/bin/env python3
"""
Simple WebSocket-based buzzer server for quiz games.
Requires: pip install websockets
"""

import asyncio
import json
import websockets
import logging
import socket
import re
import os
import threading
from datetime import datetime
from typing import Dict, Set
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BuzzerServer:
    def __init__(self):
        self.clients: Dict[websockets.WebSocketServerProtocol, dict] = {}
        self.buzzers_locked = True
        self.buzz_order = []  # Track order of buzzes
        self.admin_clients: Set[websockets.WebSocketServerProtocol] = set()

    async def register_client(self, websocket, data):
        """Register a new client (buzzer or admin)"""
        is_admin = data.get('is_admin', False)
        
        if is_admin:
            self.admin_clients.add(websocket)
            self.clients[websocket] = {
                'type': 'admin',
                'connected_at': datetime.now()
            }
            logger.info("Admin client connected")
        else:
            team_name = data.get('team_name', f'Team {len([c for c in self.clients.values() if c.get("type") == "buzzer"]) + 1}')
            
            # Check if team name is already taken
            existing_teams = [c['team_name'] for c in self.clients.values() if c.get('type') == 'buzzer']
            logger.info(f"Checking team name '{team_name}' against existing teams: {existing_teams}")
            
            if team_name in existing_teams:
                await websocket.send(json.dumps({
                    'type': 'registration_rejected',
                    'reason': 'duplicate_name',
                    'message': f'Team name "{team_name}" is already taken. Please choose a different name.'
                }))
                logger.info(f"Registration rejected for duplicate team name: {team_name}")
                return
            
            self.clients[websocket] = {
                'type': 'buzzer',
                'team_name': team_name,
                'has_buzzed': False,
                'buzz_time': None,
                'connected_at': datetime.now()
            }
            logger.info(f"Buzzer client connected: {team_name}")
        
        # Send current state to new client
        await self.send_state_update(websocket)

    async def handle_buzz(self, websocket, data):
        """Handle a buzz from a client"""
        client = self.clients.get(websocket)
        if not client or client['type'] != 'buzzer':
            return

        # Check if buzzers are locked or if this team already buzzed
        if self.buzzers_locked or client['has_buzzed']:
            await websocket.send(json.dumps({
                'type': 'buzz_rejected',
                'reason': 'locked' if self.buzzers_locked else 'already_buzzed'
            }))
            return

        # Record the buzz
        buzz_time = datetime.now()
        client['has_buzzed'] = True
        client['buzz_time'] = buzz_time
        
        # Add to buzz order
        self.buzz_order.append({
            'team_name': client['team_name'],
            'buzz_time': buzz_time.isoformat(),
            'order': len(self.buzz_order) + 1
        })

        logger.info(f"Buzz from {client['team_name']} at {buzz_time}")

        # Notify all clients
        await self.broadcast_state_update()

    async def handle_admin_command(self, websocket, data):
        """Handle admin commands"""
        if websocket not in self.admin_clients:
            logger.warning("Non-admin client attempted admin command")
            return

        command = data.get('command')
        logger.info(f"Admin command received: {command}")
        
        if command == 'reset':
            await self.reset_buzzers()
            logger.info("Buzzers reset")
        elif command == 'lock':
            self.buzzers_locked = True
            await self.reset_buzzers()
            logger.info("Buzzers locked and reset")
        elif command == 'unlock':
            self.buzzers_locked = False
            await self.broadcast_state_update()
            logger.info("Buzzers unlocked")
        else:
            logger.warning(f"Unknown admin command: {command}")

    async def reset_buzzers(self):
        """Reset all buzzers to ready state"""
        for client in self.clients.values():
            if client['type'] == 'buzzer':
                client['has_buzzed'] = False
                client['buzz_time'] = None
        
        self.buzz_order = []
        await self.broadcast_state_update()

    async def send_state_update(self, websocket):
        """Send current state to a specific client"""
        client = self.clients.get(websocket)
        if not client:
            return

        if client['type'] == 'admin':
            # Send full state to admin
            state = {
                'type': 'state_update',
                'buzzers_locked': self.buzzers_locked,
                'buzz_order': self.buzz_order,
                'teams': [
                    {
                        'team_name': c['team_name'],
                        'has_buzzed': c['has_buzzed'],
                        'buzz_time': c['buzz_time'].isoformat() if c['buzz_time'] else None
                    }
                    for c in self.clients.values() if c['type'] == 'buzzer'
                ]
            }
        else:
            # Send limited state to buzzer clients
            state = {
                'type': 'state_update',
                'buzzers_locked': self.buzzers_locked,
                'has_buzzed': client['has_buzzed'],
                'buzz_order': self.buzz_order
            }

        await websocket.send(json.dumps(state))

    async def broadcast_state_update(self):
        """Send state update to all connected clients"""
        if not self.clients:
            return

        # Create a copy of the clients dict to avoid modification during iteration
        clients_copy = dict(self.clients)
        disconnected_clients = []
        
        for websocket in clients_copy.keys():
            try:
                await self.send_state_update(websocket)
            except Exception as e:
                logger.error(f"Failed to send update to client: {e}")
                disconnected_clients.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected_clients:
            await self.handle_client_disconnect(websocket)

    async def handle_client_message(self, websocket, message):
        """Handle incoming message from client"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')

            if msg_type == 'register':
                await self.register_client(websocket, data)
            elif msg_type == 'buzz':
                await self.handle_buzz(websocket, data)
            elif msg_type == 'admin_command':
                await self.handle_admin_command(websocket, data)
            else:
                logger.warning(f"Unknown message type: {msg_type}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from client: {message}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def handle_client_disconnect(self, websocket):
        """Handle client disconnection"""
        client = self.clients.get(websocket)
        if client:
            if client['type'] == 'admin':
                self.admin_clients.discard(websocket)
                logger.info("Admin client disconnected")
            else:
                logger.info(f"Buzzer client disconnected: {client['team_name']}")
            
            del self.clients[websocket]
            await self.broadcast_state_update()

    async def client_handler(self, websocket):
        """Handle new client connections"""
        logger.info(f"New client connected from {websocket.remote_address}")
        
        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"Error in client handler: {e}")
        finally:
            await self.handle_client_disconnect(websocket)

    def get_local_ip(self):
        """Get the local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "localhost"

    def update_html_files(self, ip_address):
        """Update HTML files with the correct IP address"""
        files_to_update = ['index.html', 'admin.html']
        
        for filename in files_to_update:
            if not os.path.exists(filename):
                logger.warning(f"{filename} not found")
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
            
            # Also handle any existing IP addresses
            updated_content = re.sub(
                r"const wsUrl = 'ws://[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:8765';",
                f"const wsUrl = 'ws://{ip_address}:8765';",
                updated_content
            )
            
            # Write back to file
            with open(filename, 'w') as f:
                f.write(updated_content)
            
            logger.info(f"✓ Updated {filename} with IP {ip_address}")

    def start_http_server(self, ip_address):
        """Start HTTP server to serve HTML files"""
        class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                # Suppress HTTP server logs to keep output clean
                pass
        
        def run_http_server():
            try:
                httpd = HTTPServer(('0.0.0.0', 8080), CustomHTTPRequestHandler)
                logger.info(f"HTTP server started on http://{ip_address}:8080")
                httpd.serve_forever()
            except Exception as e:
                logger.error(f"HTTP server failed: {e}")
        
        http_thread = threading.Thread(target=run_http_server, daemon=True)
        http_thread.start()

# Remove the global server instance since we create it in main()
# buzzer_server = BuzzerServer()

async def main():
    """Start the WebSocket server"""
    logger.info("Starting buzzer server on localhost:8765")
    
    # Create server instance
    server = BuzzerServer()
    
    # Get IP and update HTML files
    ip_address = server.get_local_ip()
    server.update_html_files(ip_address)
    
    # Start HTTP server for serving HTML files
    server.start_http_server(ip_address)
    
    # Create wrapper function for the handler
    async def handler(websocket):
        await server.client_handler(websocket)
    
    start_server = websockets.serve(
        handler,
        "0.0.0.0",  # Listen on all network interfaces
        8765,
        ping_interval=20,
        ping_timeout=10
    )
    
    await start_server
    logger.info(f"WebSocket server started on ws://{ip_address}:8765")
    logger.info(f"Teams: http://{ip_address}:8080/index.html")
    logger.info(f"Admin: http://{ip_address}:8080/admin.html")
    
    # Keep server running
    await asyncio.Future()  # run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutting down...")