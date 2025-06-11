import time
import threading
from datetime import datetime, timedelta


class SimulatedClock:
    def __init__(self, sim_start: str, sim_end: str):
        self.sim_start = datetime.strptime(sim_start, "%Y-%m-%d %H:%M:%S")
        self.sim_end = datetime.strptime(sim_end, "%Y-%m-%d %H:%M:%S")
        self.sim_now = self.sim_start
        self.real_start = time.time()
        self.speed = 1.0
        self.running = False
        self.lock = threading.Lock()

    def start(self):
        self.running = True
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        while self.running and self.sim_now < self.sim_end:
            with self.lock:
                elapsed_real = time.time() - self.real_start
                self.sim_now = self.sim_start + timedelta(
                    seconds=elapsed_real * self.speed
                )
            time.sleep(0.05)

    def get_sim_time(self):
        with self.lock:
            return self.sim_now

    def set_speed(self, new_speed):
        with self.lock:
            # 更新基准
            elapsed_real = time.time() - self.real_start
            self.sim_start = self.sim_now
            self.real_start = time.time()
            self.speed = new_speed

    def forward_seconds(self, seconds):
        with self.lock:
            self.sim_now += timedelta(seconds=seconds)
            self.sim_now = max(self.sim_start, min(self.sim_now, self.sim_end))
            self.sim_start = self.sim_now
            self.real_start = time.time()

    def stop(self):
        self.running = False
