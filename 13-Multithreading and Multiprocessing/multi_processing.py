## PROCESSES THAT RUN IN PARALLEL
# CPU-BOUND TASKS: TASKS THAT ARE HEAVY ON CPU USAGE (E.G., MATHEMATICAL COMPUTATIONS, DATA PROCESSING).
# PARALLEL EXECUTION: MULTIPLE CORES OF THE CPU

import multiprocessing

import time


def square_numbers():
    for i in range(5):
        time.sleep(1)
        print(f"Square: {i*i}")


def cube_numbers():
    for i in range(5):
        time.sleep(1.5)
        print(f"Cube: {i * i * i}")


if __name__ == "__main__":

    ## CREATE 2 PROCESSES
    p1 = multiprocessing.Process(target=square_numbers)
    p2 = multiprocessing.Process(target=cube_numbers)
    t = time.time()

    ## START THE PROCESS
    p1.start()
    p2.start()

    ## WAIT FOR THE PROCESS TO COMPLETE
    p1.join()
    p2.join()

    finished_time = time.time() - t
    print(finished_time)
