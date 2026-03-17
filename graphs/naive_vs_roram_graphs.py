import matplotlib.pyplot as plt
import time
import random
import numpy as np
from tqdm import tqdm
from naive_roram import Client as NaiveRangeClient
from roram import Client as RORAMClient

def get_data_point(client_classes, writes, reads, N, Z, B):
    data_point = []
    write_queries = []
    for i in range(writes):
        a = random.randint(0, N - 1)
        end = random.randint(a, N - 1) # inclusive
        r = end - a + 1
        write_queries.append((a, r))

    read_queries = []
    for i in range(reads):
        a = random.randint(0, N - 1)
        end = random.randint(a, N - 1) # inclusive
        r = end - a + 1
        read_queries.append((a, r))

    for client_class in client_classes:
        client = client_class(N, Z=Z, B=B)
        # print(f"Initialized with N={N}, Z={Z}, B={B} bits")
        truth = np.zeros(N, dtype=int).astype(str)
        client.nice_write(0, N, truth)

        start_time = time.time()
        for i in range(writes):
            a, r = write_queries[i]
            slice = np.random.randint(0, 10, r).astype(str) # r-size array of chars 0-9
            client.nice_write(a, r, slice)
            truth[a:a+r] = slice

        write_time = time.time() - start_time
        average_write_time = write_time / writes

        start_time = time.time()
        for i in range(reads):
            a = random.randint(0, N - 1)
            a, r = read_queries[i]
            result = client.nice_read(a, r)
            assert np.array_equal(result, truth[a:a+r])

        read_time = time.time() - start_time
        average_read_time = read_time / reads
        data_point.append((average_write_time, average_read_time))
    return data_point

def get_data(Ns):
    Z, B = 4, 8192
    client_classes = [NaiveRangeClient, RORAMClient]
    basic_write_data = []
    basic_read_data = []
    recursive_write_data = []
    recursive_read_data = []
    for N in tqdm(Ns):
        (basic_write_time, basic_read_time), (recursive_write_time, recursive_read_time) = get_data_point(client_classes, 100, 100, N, Z, B)
        basic_write_data.append(basic_write_time)
        basic_read_data.append(basic_read_time)
        recursive_write_data.append(recursive_write_time)
        recursive_read_data.append(recursive_read_time)
    return np.array(basic_write_data), np.array(basic_read_data), np.array(recursive_write_data), np.array(recursive_read_data)

def plot_data():
    # Ns = np.arange(1_000, 10_000, 1_000) #, 5_000] #10_000] #, 100_000, 1_000_000]
    # Ns = np.arange(100, 1_000, 100)
    Ns = np.arange(10, 100, 10)
    basic_write_data, basic_read_data, recursive_write_data, recursive_read_data = get_data(Ns)
    plt.subplot(1, 2, 1)
    plt.title("Average Write Time vs N for Naive Range ORAM and RORAM")
    plt.xlabel("N")
    plt.ylabel("Time (microseconds)")
    plt.plot(Ns, basic_write_data * 1_000_000, label="Naive") 
    plt.plot(Ns, recursive_write_data * 1_000_000, label="RORAM")
    plt.legend()

    plt.subplot(1, 2, 2)
    plt.title("Average Read Time vs N for Naive Range ORAM and RORAM")
    plt.xlabel("N")
    plt.ylabel("Time (microseconds)")
    plt.plot(Ns, basic_read_data * 1_000_000, label="Naive") 
    plt.plot(Ns, recursive_read_data * 1_000_000, label="RORAM")
    plt.legend()
    plt.show()

if __name__ == "__main__":
    plot_data()
