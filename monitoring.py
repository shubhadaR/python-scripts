import psutil

cpu_threshold= 90
mem_threshold= 90


def monitor_system():

    cpu= psutil.cpu_percent()
    mem= psutil.virtual_memory().percent

    if cpu > cpu_threshold:
        print(f"High cpu usage{cpu}")
    if mem > mem_threshold:
        print(f"High mem usage{mem}")
