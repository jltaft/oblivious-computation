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
        client = client_class(N, Z=Z, B=B)
        print('init')
        client.nice_write(0, N, truth)

        print('ready')
        for r, a_rs in tqdm(zip(rs, queries)):
            client.reset_seeks()
            r_start_time = time.time()
            for a in a_rs:
                result = client.nice_read(a, r)
                assert np.array_equal(result, truth[a:a+r])
            r_average_time = (time.time() - r_start_time) / num_reads
            r_average_seeks = client.get_seeks() / num_reads
            access_data.append(r_average_time)
            seeks_data.append(r_average_seeks)
        access_datas.append(np.array(access_data))
        seeks_datas.append(np.array(seeks_data))

    return access_datas, seeks_datas


def plot_data():
    N, Z, B = 2 ** 13, 4, 8192
    rs = np.array([2 ** i for i in range(14)])
    num_reads = 3
    access_datas, seeks_datas = get_data([NaiveRangeClient, RORAMClient], rs, num_reads, N, Z, B)
    naive_access_data, naive_seeks_data = access_datas[0], seeks_datas[0]
    roram_access_data, roram_seeks_data = access_datas[1], seeks_datas[1]
    plt.subplot(1, 2, 1)
    plt.title("Average Access Time vs r for Naive Range ORAM and RORAM")
    plt.xlabel("R")
    plt.ylabel("Time (microseconds)")
    plt.plot(rs, naive_access_data * 1_000_000, label="Naive") 
    plt.plot(rs, roram_access_data * 1_000_000, label="RORAM")
    plt.legend()

    plt.subplot(1, 2, 2)
    plt.title(f"# of seeks vs r for Naive Range ORAM and RORAM")
    plt.xlabel("R")
    plt.ylabel("Seeks")
    plt.plot(rs, naive_seeks_data, label="Naive") 
    plt.plot(rs, roram_seeks_data, label="RORAM")
    plt.legend()
    plt.show()

if __name__ == "__main__":
    plot_data()
