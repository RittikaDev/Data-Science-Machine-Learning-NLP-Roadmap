### MULTITHREADING
## WHEN TO USE MULTI THREADING
### I/O-BOUND TASKS: TASKS THAT SPEND MORE TIME WAITING FOR I/O OPERATIONS (E.G., FILE OPERATIONS, NETWORK REQUESTS).
### CONCURRENT EXECUTION: WHEN YOU WANT TO IMPROVE THE THROUGHPUT OF YOUR APPLICATION BY PERFORMING MULTIPLE OPERATIONS CONCURRENTLY.

import threading
import time


def print_numbers():
    for i in range(5):
        time.sleep(2)
        print(f"Number:{i}")


def print_letter():
    for letter in "abcde":
        time.sleep(2)
        print(f"Letter: {letter}")


## CREATE 2 THREADS
t1 = threading.Thread(target=print_numbers)
t2 = threading.Thread(target=print_letter)

t = time.time()
## START THE THREAD
t1.start()
t2.start()

### WAIT FOR THE THREADS TO COMPLETE
t1.join()
t2.join()

finished_time = time.time() - t
print(finished_time)
