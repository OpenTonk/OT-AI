# pseudocode client
start tankcontroller
start comms client in a thread.
start streaming client.

## on get frame
if usepicam then get frame from picamerathread.
else get frame from on_get_frame event.

## on message
set tankcontroller drive speed and steer angle.