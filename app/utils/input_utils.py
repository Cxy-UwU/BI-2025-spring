import csv
import json
import os
import threading
import atexit
from datetime import datetime


class DataProvider:
    def __init__(self):
        self.source_path = "../data_source/exposure_sorted.csv"
        self.config_path = "input_config.json"
        self.target_path = "../../logs/target.log"
        self._file = open(self.source_path, newline='', encoding='utf-8')
        self._reader = csv.DictReader(self._file)
        self._header = self._reader.fieldnames
        self._current_time = None
        self._buffered_row = None
        self._transfer_thread = None
        self._stop_event = threading.Event()
        self._load_state_or_init()
        atexit.register(self._save_state)

    def _parse_time(self, timestr):
        return datetime.strptime(timestr, "%Y-%m-%d %H:%M:%S").timestamp()

    def _load_state_or_init(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                self._current_time = state.get("current_time")
            except Exception:
                pass

        if self._current_time is None:
            # 单独读取第一行时间
            with open(self.source_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                first_row = next(reader, None)
                if first_row:
                    self._current_time = self._parse_time(first_row["exposure_time"])

        # 重新初始化 reader
        self._file.seek(0)
        self._reader = csv.DictReader(self._file)

    def _save_state(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump({"current_time": self._current_time}, f)
        except Exception:
            pass

    def forward(self, seconds):
        self._current_time += seconds
        emitted = []
        while True:
            row = self._buffered_row or next(self._reader, None)
            if not row:
                return "\n".join([",".join([str(v) for v in row.values()]) for row in emitted]), False  # 读完了
            if self._parse_time(row["exposure_time"]) <= self._current_time:
                emitted.append(row)
                self._buffered_row = None
            else:
                self._buffered_row = row
                break
        return "\n".join([(",".join([str(v) for v in row.values()])) for row in emitted]) + '\n', True

    def start_transfer(self, gap=5, stride=1):
        def run():
            import time
            while not self._stop_event.is_set():
                batch, has_more = self.forward(stride)
                print(batch, end="")
                if not has_more:
                    print("✅ 所有数据已转发完毕。自动退出线程。")
                    break
                time.sleep(gap)

        self._transfer_thread = threading.Thread(target=run, daemon=True)
        self._transfer_thread.start()

    def stop_transfer(self):
        self._stop_event.set()
        if self._transfer_thread:
            self._transfer_thread.join()


if __name__ == "__main__":
    dp = DataProvider()
    dp.start_transfer(gap=2, stride=1)
    try:
        while dp._transfer_thread.is_alive():
            dp._transfer_thread.join(timeout=1)
    except KeyboardInterrupt:
        dp.stop_transfer()
        print("⛔ 手动中断，退出。")
