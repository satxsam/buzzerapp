# Quiz Buzzer Setup Guide

## Quick Start

### 1. Install Python Dependencies
```bash
pip install websockets
```

### 2. Start the Server
```bash
python server.py
```

You should see:
```
INFO:__main__:Starting buzzer server on localhost:8765
INFO:__main__:Buzzer server started! Connect clients to ws://localhost:8765
```

### 3. Open the Client Files
- **For teams:** Open `index.html` in a web browser
- **For admin:** Open `admin.html` in a web browser

### 4. Connect Teams
1. Each team opens `index.html` on their phone/tablet/computer
2. Enter a team name (e.g., "Team Alpha")
3. Click "Join Game"
4. The buzzer interface should appear

### 5. Admin Control
1. Open `admin.html` 
2. It will automatically connect as admin
3. Use the buttons to control the game:
   - **Unlock Buzzers** - Allow teams to buzz in
   - **Lock Buzzers** - Prevent buzzing (between questions)
   - **Reset Buzzers** - Clear all buzzes for next question

## Troubleshooting

### "Failed to connect to server"
- Make sure `python server.py` is running
- Check that you see "Buzzer server started!" message
- Try refreshing the web page

### Teams can't buzz in
- Make sure admin has clicked "Unlock Buzzers"
- Check that the team hasn't already buzzed for this question

### Connection lost
- The server may have stopped running
- Restart with `python server.py`
- Teams will need to refresh and reconnect

## Game Flow Example

1. **Setup Phase:**
   - Start server: `python server.py`
   - Teams connect via `index.html`
   - Admin opens `admin.html`

2. **During Questions:**
   - Admin clicks "Lock Buzzers" (default state)
   - Read the question
   - Admin clicks "Unlock Buzzers"
   - Teams can now buzz in
   - First team to buzz appears at top of admin list

3. **Between Questions:**
   - Admin clicks "Reset Buzzers"
   - Buzzers are automatically locked
   - Ready for next question

## Network Setup (Optional)

To use across different devices on the same network:

1. Find your computer's IP address:
   ```bash
   # Windows
   ipconfig
   
   # Mac/Linux
   ifconfig
   ```

2. Edit both HTML files and change:
   ```javascript
   const wsUrl = 'ws://localhost:8765';
   ```
   to:
   ```javascript
   const wsUrl = 'ws://YOUR_IP_ADDRESS:8765';
   ```

3. Update the server to accept external connections:
   ```python
   # In server.py, change:
   start_server = websockets.serve(
       buzzer_server.client_handler,
       "0.0.0.0",  # Changed from "localhost"
       8765,
       ping_interval=20,
       ping_timeout=10
   )
   ```

Now teams can connect from any device on your network!