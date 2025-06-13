import time
import csv
import json
import os
import sys
from datetime import datetime


class DataProvider:
    def __init__(self):
        self.source_path = os.path.join(os.path.dirname(__file__), 'app', 'data_source', 'exposure_sorted_dedup.csv')
        self.config_path = os.path.join(os.path.dirname(__file__), 'input_config.json')
        self.target_path = os.path.join(os.path.dirname(__file__), 'logs', 'target.log')
        self._file = open(self.source_path, newline='', encoding='utf-8')
        self._reader = csv.DictReader(self._file)
        self._header = self._reader.fieldnames
        self._current_time = None
        self._buffered_row = None
        self._load_state_or_init()

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
        self._save_state()
        return "\n".join([(",".join([str(v) for v in row.values()])) for row in emitted]) + '\n', True


if __name__ == "__main__":
    # 支持命令行参数 speed
    speed = 1
    if len(sys.argv) > 1:
        try:
            speed = int(sys.argv[1])
        except Exception:
            pass

    dp = DataProvider()

    while True:
        batch, has_more = dp.forward(5 * speed)
        with open(dp.target_path, "a", encoding="utf-8", newline='\n') as f:
            f.write(batch)
            f.flush()
            os.fsync(f.fileno())
        print(batch, flush=True)
        if not has_more:
            print("✅ 所有数据已转发完毕。")
            break
        time.sleep(5)