# pseudocode client
1. start tankcontroller
2. start comms client in a thread.
3. start streaming client.

## on get frame
1. if usepicam then get frame from picamerathread.
2. else get frame from on_get_frame event.

## on message
set tankcontroller drive speed and steer angle.