import matplotlib.pyplot as plt
import time
import random
import numpy as np
from tqdm import tqdm
import copy
from basic_path_oram import Client as BasicClient
from re_recursive_path_oram import Client as RecursiveClient


def get_data_point(client_classes, writes, reads, N, Z, B):
    data_point = []
    write_indices = [random.randint(0, N - 1) for _ in range(writes)]
    read_indices = copy.copy(write_indices)
    random.shuffle(read_indices)

    for client_class in client_classes:
        client = client_class(N, Z=Z, B=B)
        truth = {}
        # Write random data to all blocks
        client.reset_seeks()
        start_time = time.time()
        for i in range(writes):
            data = str(random.randint(0, 10))
            truth[write_indices[i]] = data
            client.access("write", write_indices[i], data)

        write_time = time.time() - start_time
        average_write_time = write_time / writes

        start_time = time.time()
        for i in range(reads):
            idx = read_indices[i]
            val = client.access("read", idx)
            assert val == truth[idx]

        read_time = time.time() - start_time
        average_read_time = read_time / reads
        data_point.append((average_write_time, average_read_time, client.get_seeks() / (writes + reads)))
    return data_point

def get_data(Ns, writes, reads):
    Z, B = 4, 8192
    client_classes = [BasicClient, RecursiveClient]
    basic_write_data = []
    basic_read_data = []
    basic_seeks_data = []
    recursive_write_data = []
    recursive_read_data = []
    recursive_seeks_data = []
    for N in tqdm(Ns):
        (basic_write_time, basic_read_time, basic_seeks), (recursive_write_time, recursive_read_time, recursive_seeks) = get_data_point(client_classes, writes, reads, N, Z, B)
        basic_write_data.append(basic_write_time)
        basic_read_data.append(basic_read_time)
        basic_seeks_data.append(basic_seeks)
        recursive_write_data.append(recursive_write_time)
        recursive_read_data.append(recursive_read_time)
        recursive_seeks_data.append(recursive_seeks)
    return np.array(basic_write_data), np.array(basic_read_data), np.array(basic_seeks_data), np.array(recursive_write_data), np.array(recursive_read_data), np.array(recursive_seeks_data)

def plot_data():
    Ns = np.arange(1_000, 10_000, 1_000) #, 5_000] #10_000] #, 100_000, 1_000_000]
    # Ns = np.arange(100, 1_000, 100)
    writes = 100
    reads = 100
    basic_write_data, basic_read_data, basic_seeks_data, recursive_write_data, recursive_read_data, recursive_seeks_data = get_data(Ns, writes, reads)
    plt.subplot(1, 3, 1)
    plt.title("Average Write Time vs N for Basic and Recursive Path ORAM")
    plt.xlabel("N")
    plt.ylabel("Time (microseconds)")
    plt.plot(Ns, basic_write_data * 1_000_000, label="basic") 
    plt.plot(Ns, recursive_write_data * 1_000_000, label="recursive")
    plt.legend()

    plt.subplot(1, 3, 2)
    plt.title("Average Read Time vs N for Basic and Recursive Path ORAM")
    plt.xlabel("N")
    plt.ylabel("Time (microseconds)")
    plt.plot(Ns, basic_read_data * 1_000_000, label="basic") 
    plt.plot(Ns, recursive_read_data * 1_000_000, label="recursive")
    plt.legend()
    
    plt.subplot(1, 3, 3)
    plt.title(f"Average seeks per query vs N for Basic and Recursive Path ORAM ()")
    plt.xlabel("N")
    plt.ylabel("Average seeks")
    plt.plot(Ns, basic_seeks_data, label="basic") 
    plt.plot(Ns, recursive_seeks_data, label="recursive")
    plt.legend()
    plt.show()

if __name__ == "__main__":
    plot_data()
