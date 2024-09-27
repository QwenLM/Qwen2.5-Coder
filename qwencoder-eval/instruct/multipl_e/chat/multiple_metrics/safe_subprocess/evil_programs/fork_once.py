import os
import time

if os.fork() == 0:
    while True:
        time.sleep(60)
