# pseudocode server
Start comms socket server in a thread.
Start streaming socket server.

## on frame
detect lanes.
calculate steering angle based on lanes.
send steering angle to client trough comm server.
display frame with lanes and steering anlge lines.

## on disconnect
disconnect comms server.
