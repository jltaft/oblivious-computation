import matplotlib.pyplot as plt
import time
import random
import numpy as np
from tqdm import tqdm
from naive_roram import Client as NaiveRangeClient
from roram import Client as RORAMClient

def get_data(client_classes, rs, num_reads, N, Z, B):
    access_datas = []
    seeks_datas = []

    queries = []
    for r in rs:
        queries.append([random.randint(0, N - r) for _ in range(num_reads)])

    truth = np.random.randint(0, 1000, size=N).astype(str)

    for client_class in client_classes:
        access_data = []
        seeks_data = []
        print(f"\n\nInitializing {client_class}")
        client = client_class(N, Z=Z, B=B, initial_data=truth)
        print('Initialized')

        for r, a_rs in zip(rs, queries):
            print(f"r: {r}")
            client.reset_seeks()
            r_start_time = time.time()
            for a in a_rs:
                result = client.nice_read(a, r)
                assert np.array_equal(result, truth[a:a+r])
            r_average_time = (time.time() - r_start_time) / num_reads
            r_average_seeks = client.get_seeks() / num_reads
            access_data.append(r_average_time)
            seeks_data.append(r_average_seeks)
            print(f'Avg time: {r_average_time}')
            print(f'Avg seeks: {r_average_seeks}')
        access_datas.append(np.array(access_data))
        seeks_datas.append(np.array(seeks_data))

    return access_datas, seeks_datas


def plot_data():
    power_of_two = 15
    N, Z, B = 2 ** power_of_two, 4, 8192
    rs = np.array([2 ** i for i in range(power_of_two)])
    num_reads = 1
    access_datas, seeks_datas = get_data([RORAMClient, NaiveRangeClient], rs, num_reads, N, Z, B)
    naive_access_data, naive_seeks_data = access_datas[1], seeks_datas[1]
    roram_access_data, roram_seeks_data = access_datas[0], seeks_datas[0]

    plt.subplot(1, 4, 1)
    plt.title("Average Access Time vs r for Naive Range ORAM and RORAM")
    plt.xlabel("R")
    plt.ylabel("Time (s)")
    plt.plot(rs, naive_access_data, label="Naive") 
    plt.plot(rs, roram_access_data, label="RORAM")
    plt.legend()
    plt.ylim(ymin=0)

    plt.subplot(1, 4, 2)
    plt.title(f"# of seeks vs r for Naive Range")
    plt.xlabel("R")
    plt.ylabel("Seeks")
    plt.plot(rs, naive_seeks_data, label="Naive") 
    plt.plot(rs, roram_seeks_data, label="RORAM")
    plt.legend()
    plt.ylim(ymin=0)

    plt.subplot(1, 4, 3)
    plt.title(f"# of seeks vs r for Naive Range")
    plt.xlabel("R")
    plt.ylabel("Seeks")
    plt.plot(rs, naive_seeks_data, label="Naive") 
    plt.legend()
    plt.ylim(ymin=0)

    plt.subplot(1, 4, 4)
    plt.title(f"# of seeks vs r for RORAM")
    plt.xlabel("R")
    plt.ylabel("Seeks")
    plt.plot(rs, roram_seeks_data, label="RORAM")
    plt.legend()
    plt.ylim(ymin=0)
    plt.show()

if __name__ == "__main__":
    plot_data()
