# pseudocode server
1. Start comms socket server in a thread.
2. Start streaming socket server.

## on frame
1. detect lanes.
2. calculate steering angle based on lanes.
3. send steering angle to client trough comm server.
4. display frame with lanes and steering anlge lines.

## on disconnect
disconnect comms server.
