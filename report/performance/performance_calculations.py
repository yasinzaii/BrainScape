import time
import psutil
import pynvml
import resource
import subprocess
from codecarbon import EmissionsTracker

if __name__ == "__main__":
    
    # Initialize GPU monitoring (pynvml)
    pynvml.nvmlInit()
    gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0) 
    
    # Polling interval in seconds
    interval = 1.0
    
    # Initialize and Start Emission Tracker
    tracker = EmissionsTracker(
        output_file="report/performance/emissions.csv",  # CSV file name
        # You can optionally set country_iso_code, etc. for region-specific factors
    )
    tracker.start()
    
    start_time = time.time()
    start_cpu  = resource.getrusage(resource.RUSAGE_CHILDREN)
    
    
    # Start the pipeline as a subprocess
    pipeline_command = [
        "python", "./src/prepare_dataset.py", 
        "--config-path=report/performance/perf_conf/config.json"
    ]
    process = subprocess.Popen(pipeline_command)
    
    
    # Lists to store usage metrics over time
    gpu_mem_usages = []
    gpu_utilizations = []
    cpu_usage_percentages = []
    
    
    while True:
        
        # Check if process is done
        retcode = process.poll()
        # If the pipeline is finished, break out
        if retcode is not None:
            break
        
        # GPU Memoery and Utilization Info.
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(gpu_handle)
        util_info = pynvml.nvmlDeviceGetUtilizationRates(gpu_handle)
        # GPU memory usage in MB
        gpu_mem_usages.append(mem_info.used / (1024**2))
        # GPU utilization in %
        gpu_utilizations.append(util_info.gpu)
        
        # CPU Utilization Info.
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_usage_percentages.append(cpu_percent)

        
        # Sleep for the polling interval
        time.sleep(interval)
        
        
    end_time = time.time()
    end_cpu  = resource.getrusage(resource.RUSAGE_CHILDREN)
    
    
    
    wall_clock = end_time - start_time
    user_cpu_time = end_cpu.ru_utime - start_cpu.ru_utime  # user CPU time
    system_cpu_time = end_cpu.ru_stime - start_cpu.ru_stime   # system CPU time
    
    
    # Stop Emissions Tracker
    emissions = tracker.stop()
    
    print(f"Num Samples: {len(gpu_utilizations)}")
    print("")
    print(f"Peak GPU Memory Usage: {max(gpu_mem_usages):.2f} MB")
    print(f"Peak GPU Utilization: {max(gpu_utilizations):.2f}%")
    print(f"Average GPU Utilization: {sum(gpu_utilizations) / len(gpu_utilizations):.2f}%")
    
    print("")
    print(f"Number of CPU cores: {psutil.cpu_count(logical=True)}")
    print(f"Average CPU usage: {sum(cpu_usage_percentages) / len(cpu_usage_percentages):.2f}%")
    
    print("")
    print(f"Total CPU time: {user_cpu_time + system_cpu_time} s")
    print(f"Wall-clock time: {wall_clock} s")
    
    print("")
    print(emissions)