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

        client.reset_seeks()
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
        data_point.append((average_write_time, average_read_time, client.get_seeks()))
    return data_point

def get_data(Ns, writes, reads):
    Z, B = 4, 8192
    client_classes = [NaiveRangeClient, RORAMClient]
    naive_write_data = []
    naive_read_data = []
    naive_seeks_data = []
    roram_write_data = []
    roram_read_data = []
    roram_seeks_data = []
    for N in tqdm(Ns):
        (naive_write_time, naive_read_time, naive_seeks), (roram_write_time, roram_read_time, roram_seeks) = get_data_point(client_classes, writes, reads, N, Z, B)
        naive_write_data.append(naive_write_time)
        naive_read_data.append(naive_read_time)
        naive_seeks_data.append(naive_seeks)

        roram_write_data.append(roram_write_time)
        roram_read_data.append(roram_read_time)
        roram_seeks_data.append(roram_seeks)
    return np.array(naive_write_data), np.array(naive_read_data), np.array(naive_seeks_data), np.array(roram_write_data), np.array(roram_read_data), np.array(roram_seeks_data)

def plot_data():
    # Ns = np.arange(1_000, 10_000, 1_000) #, 5_000] #10_000] #, 100_000, 1_000_000]
    Ns = np.arange(10, 51, 20)
    # Ns = np.arange(10, 100, 10)
    writes = 100
    reads = 100
    naive_access_data, naive_seeks_data, roram_access_data, roram_seeks_data = get_data(Ns, writes, reads)
    plt.subplot(1, 2, 1)
    plt.title("Average Access Time vs N for Naive Range ORAM and RORAM")
    plt.xlabel("N")
    plt.ylabel("Time (microseconds)")
    plt.plot(Ns, naive_access_data * 1_000_000, label="Naive") 
    plt.plot(Ns, roram_access_data * 1_000_000, label="RORAM")
    plt.legend()

    plt.subplot(1, 2, 2)
    plt.title(f"# of seeks vs r for Naive Range ORAM and RORAM")
    plt.xlabel("N")
    plt.ylabel("Seeks")
    plt.plot(Ns, naive_seeks_data, label="Naive") 
    plt.plot(Ns, roram_seeks_data, label="RORAM")
    plt.legend()
    plt.show()

if __name__ == "__main__":
    plot_data()
