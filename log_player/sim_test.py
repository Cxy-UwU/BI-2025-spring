from simulated_clock import SimulatedClock
import time

sim_clock: SimulatedClock = SimulatedClock(
    sim_start="2019-06-13 17:00:00", sim_end="2019-07-12 16:59:53"
)

sim_clock.start()

sim_clock.forward_seconds(60 * 60 * 24)


while True:
    current_time = sim_clock.get_sim_time()
    print(f"Simulated time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    time.sleep(0.2)
