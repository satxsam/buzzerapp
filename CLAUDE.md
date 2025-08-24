# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Quiz Buzzer App** - a real-time WebSocket-based quiz buzzer system for educational or competitive quiz games. Teams connect via web browsers to buzz in for questions, while an admin controls the game flow.

### Architecture

- **Backend**: Python WebSocket server (`server.py`) handling real-time communication
- **Frontend**: Two HTML/CSS/JavaScript clients:
  - `index.html` - Team buzzer interface
  - `admin.html` - Admin control panel
- **Communication**: WebSocket protocol for real-time state synchronization

## Development Commands

### Start the Server
```bash
python server.py
```
Server starts on `localhost:8765` by default and listens on all interfaces (`0.0.0.0`).

### Dependencies
```bash
pip install websockets
```
Only dependency is the `websockets` library for Python.

### Testing the Application
1. Start server: `python server.py`
2. Open `index.html` in browser(s) for teams
3. Open `admin.html` in browser for game control
4. No automated tests - manual testing via browser interfaces

### Network Configuration
Run the network setup script to configure for multi-device access:
```bash
python setup_network.py
```
This script finds your IP address and updates HTML files to use the network IP instead of localhost.

## Key Components

### BuzzerServer Class (`server.py:18`)
Core server logic managing:
- Client registration (teams vs admin)
- Buzz handling with timing and order tracking
- Admin commands (lock/unlock/reset)
- WebSocket connection management

### WebSocket Message Types
- `register` - Client registration (team_name for buzzers, is_admin for admin)
- `buzz` - Team buzz attempt
- `admin_command` - Admin controls (reset, lock, unlock)
- `state_update` - Server state broadcast to clients

### Client State Management
Both HTML files hardcode WebSocket URL at lines:
- `index.html:282` - Team client WebSocket connection
- `admin.html:336` - Admin client WebSocket connection

## Game Flow Architecture

1. **Setup**: Admin connects, teams register with names
2. **Question Phase**: Admin unlocks buzzers, teams can buzz in
3. **Response Phase**: First buzzer locks out others, buzz order tracked
4. **Reset**: Admin resets for next question

The server maintains buzz order with timestamps and prevents duplicate buzzes per round.

## Important Notes

- Server auto-locks buzzers after reset
- All clients receive real-time state updates
- Admin interface shows team count, buzz count, and buzz order
- Network setup modifies HTML files in-place for IP configuration
- No persistence - all state is in-memory only