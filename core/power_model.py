import json, os, time, math
from collections import deque

# AppData Path Setup
APP_NAME = "SEPRO"
APP_DIR = os.path.join(os.getenv('LOCALAPPDATA'), APP_NAME)

if not os.path.exists(APP_DIR):
    os.makedirs(APP_DIR)

BASELINE_FILE = os.path.join(APP_DIR, "baseline_store.json")
# End Path Setup 


def load_baseline():
    if not os.path.exists(BASELINE_FILE):
        return {}
    try:
        with open(BASELINE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_baseline(data):
    with open(BASELINE_FILE, "w") as f:
        json.dump(data, f, indent=2)

class PowerModel:
    CPU_WEIGHT = 0.7
    MEM_WEIGHT = 0.2
    DISK_WEIGHT = 0.1

    @staticmethod
    def compute_score(cpu_p, mem_mb, disk_mb_s):
        cpu_norm = min(cpu_p/100, 1.0)
        mem_norm = min(mem_mb/4000, 1.0)
        disk_norm = min(disk_mb_s/200, 1.0)

        return (
            cpu_norm * PowerModel.CPU_WEIGHT +
            mem_norm * PowerModel.MEM_WEIGHT +
            disk_norm * PowerModel.DISK_WEIGHT
        )

class ProcessProfile:
    def __init__(self, name):
        self.name = name
        self.mean = 0.05
        self.var = 0.001
        self.std = math.sqrt(self.var)
        self.last_samples = deque(maxlen=5)
        self.last_update = time.time()
        self.first_seen = time.time() # This will be set by load()

    def update(self, value):
        alpha = 0.1
        old_mean = self.mean

        self.mean = old_mean + alpha * (value - old_mean)
        self.var = self.var + alpha * (((value - old_mean)**2) - self.var)
        self.std = math.sqrt(max(self.var, 1e-6))
        self.last_samples.append(value)

class AnomalyDetector:

    NEW_PROCESS_GRACE_PERIOD = 30 # in seconds
    
    THRESH_STD = 2
    THRESH_DRIFT = 1.6
    MIN_RULES = 5
    MIN_OBS = 3

    def __init__(self):
        self.baseline = {}
        self.load()

    def load(self):
        data = load_baseline()
        current_time = time.time() # Get the current time
        
        for name, d in data.items():
            p = ProcessProfile(name)
            p.mean = d.get("mean", 0.05)
            p.var = d.get("var", 0.001)
            p.std = math.sqrt(p.var)
            
            p.first_seen = d.get("first_seen", current_time) 
            
            self.baseline[name] = p

    def save(self):
        data = {}
        for name, p in self.baseline.items():
            data[name] = {
                "mean": p.mean, 
                "var": p.var,
                "first_seen": p.first_seen 
            }
        save_baseline(data)

    def check(self, name, score):
        if name not in self.baseline:
            self.baseline[name] = ProcessProfile(name)

        p = self.baseline[name]
        
        current_time = time.time()
        if (current_time - p.first_seen) < self.NEW_PROCESS_GRACE_PERIOD:
            p.update(score) # Update to learn, but don't check for anomalies
            return False, 0 # Return "not suspicious"


        # Continue with existing logic only if grace period is over
        p.update(score)

        if len(p.last_samples) < self.MIN_OBS:
            return False, 0

        rules = 0

        if score > p.mean + self.THRESH_STD * p.std: rules += 1
        if score > p.mean * self.THRESH_DRIFT: rules += 1
        if sum(v > p.mean * 1.8 for v in p.last_samples) >= 3: rules += 1
        if len(p.last_samples) >= 5 and score > p.last_samples[-5] * 1.6: rules += 1
        if sum(v > p.mean * 1.4 for v in p.last_samples) >= 4: rules += 1

        return (rules >= self.MIN_RULES), rules