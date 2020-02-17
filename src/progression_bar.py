# Python 3.7 Built-in packages
import threading
import math
import queue

# Local packages
from src import texts, config


class ProgressionBar(object):
    def __init__(self, num, queue: queue.Queue):
        self.max_len: int = num
        self.current_value: int = 0
        self.queue: queue.Queue = queue
        self.printed_symbol_number: int = 0
        self._progression_thr = threading.Thread(
            target=self._watch_progression
        )

    def initialize(self):
        print(texts.progression_ruler, end='')  # Show job's progression

    def watch_progression(self):
        self._progression_thr.start()

    def _watch_progression(self):
        while self.current_value < self.max_len:
            try:
                self.queue.get(timeout=60)
                # print("Recieving signal")
                self.increment()
            except queue.Empty:
                print("\nProcesses terminates without completing jobs. Output result might not be complete.\n")
                break

    def write_progression(self):
        print(config.PROGRESSION_SYMBOL, end='', flush=True)

    def increment(self):
        new_value = self.current_value + 1
        if math.floor(self.current_value) != math.floor(new_value):
            progression_percentage = (
                math.floor(self.current_value / self.max_len * 100)
                , math.floor(new_value / self.max_len * 100)
            )
            # print(progression_percentage)
            for i in range(progression_percentage[1] - progression_percentage[0]):
                self.write_progression()
                self.printed_symbol_number += 1

        self.current_value = new_value
        if self.current_value == self.max_len:
            while self.printed_symbol_number < 100:
                self.write_progression()