# Python 3.7 Built-in packages
import threading
import queue
import typing
from pathlib import Path

# Local packages
from . import config
from .config import Target_Id, Database_Id, Score


def result_list_from_dict(
        d: typing.Dict[Target_Id, typing.List[typing.Tuple[Database_Id, Score]]]
) -> typing.List[typing.Tuple[Target_Id, Database_Id, Score]]:

    results_list = []
    [[results_list.append(final_l) for final_l in lrl] for lrl in [[(rl[0], db_id, score) for db_id, score in rl[1]] for rl in  d.items()]]
    return results_list


class OutputObject(object):

    def __init__(self, output_stream, output_format, max_target: int, show_info: bool):
        self._max_target = max_target
        self.file_name = "out/output.txt"
        self.csv_delimiter = config.DEFAULT_CSV_DELIMITER
        self.show_info = show_info
        self.info_dict = {}
        self.molecules_number: int = 0
        self.output_queue: queue.Queue
        self._csv_num_row = 0
        self._output_thr = threading.Thread(  # Start thread of output watching
            target=self._watch_output
        )
        self._file: Path = Path(self.file_name)

        self.formatting_function = {
            config.DEFAULT_OUTPUT_FORMAT: self.human_readable_file_formatting
            , config.CSV_FILE_FORMAT: self.csv_formatting
        }[output_format]
        self.output_function = {
            0: self.stdout_basic
            , 1: self.write_string
        }[output_stream]

    def __call__(self, *args, **kwargs):
        self.info_dict = args[2]
        self.output_function(*args[:-1])

    @property
    def file(self) -> Path:
        return self._file

    @file.setter
    def file(self, name: str):
        self.file_name = name
        self._file = Path(name)


    def slice_result_list(self, l: typing.List[typing.Tuple[Target_Id, Database_Id, Score]]):
        if self._max_target > 1:
            return l[:self._max_target]
        else:
            return l

    def stdout_basic(self, s: str):
        """
        Output the basic result string to stdout
        """
        print(s)

    def human_readable_file_formatting(self, match_results_dict: typing.Dict[Target_Id, typing.List[typing.Tuple[Database_Id, Score]]], molecule_name: str):
        """
        Output the basic result string to file
        """
        s0 = "Compound : >{}<".format(molecule_name)
        s1 = "{:<35}{:5}".format(s0, "")
        si = "{:15}{}"
        s_data = []
        i = 1
        # Build result array for sorting and iteration purpose
        match_results_list = result_list_from_dict(match_results_dict)
        l = self.slice_result_list(sorted(match_results_list, key=lambda x: x[2], reverse=True))
        if len(l) == 0:
            s_data.append(si.format("", "No hit."))
        else:
            for target_id, db_id, score in l:
                for info_list in self.info_dict.get(target_id, [{}]):
                    s_data.append(si.format( # If more than 1 information, duplicate the row
                        ''
                        , '{:<10} {:<10} {:>7}  {:<10} {}'.format(
                            i
                            , db_id
                            , "{: 2.03f}".format(score)
                            , target_id
                            , ' '.join(info_list.values())
                        )
                    ))
                i += 1
        _result_string = s1 + '\n' + '\n'.join(s_data) + '\n'
        return _result_string

    def csv_formatting(self, match_results_dict: typing.Dict[Target_Id, typing.List[typing.Tuple[Database_Id, Score]]], molecule_name: str):

        s = ""
        if self._csv_num_row == 0:  # If this is the first call

            if len(self.info_dict.values()) > 0:
                info_keys = self.info_dict.values()[0][0].keys()
            else:
                info_keys = ()

            row = [
                'query_name'
                , 'database_molecule_id'
                , 'target_id'
                , 'score'
                , *info_keys  # Data from this dictionary should always have the same keys, even if empty
            ]
            s += self.csv_delimiter.join(row) + '\n'
            self._csv_num_row = len(row)

        match_results_list = result_list_from_dict(match_results_dict)
        l = self.slice_result_list(sorted(match_results_list, key=lambda x: x[2], reverse=True))
        num_row = self._csv_num_row

        with self.file.open('a', encoding=config.ENCODING) as f:
            for target_id, db_id, score in l:
                for info_list in self.info_dict.get(target_id, [{}]):
                    row = []
                    row.append(molecule_name)
                    row.append(db_id)
                    row.append(target_id)
                    row.append(score)
                    row.extend(info_list.values())
                    while len(row) < num_row:
                        row.append('')
                    s += self.csv_delimiter.join([str(r) for r in row]) + '\n'

        return s

    def write_string(self, s: str):
        with self.file.open('a', encoding=config.ENCODING) as f:
            f.write(s)

    def process_output(self, *args):
        s = self.formatting_function(*args)
        self.output_function(s)

    def _watch_output(self):  # Loop over the number of molecules and wait for a queue update
        i = 0
        while i < self.molecules_number:
            try:
                self.process_output(*self.output_queue.get(timeout=60))
            except queue.Empty:
                print("\nProcesses terminates without completing jobs. Output result might not be complete.\n")
                break

            i += 1

    def watch_output(self, shared_info, queue: queue.Queue, molecules_number: int):
        self.molecules_number = molecules_number
        self.output_queue = queue
        # if self.show_info:
        #     self.info_dict = shared_info
        self.info_dict = shared_info
        self._output_thr.start()

    def wait(self):
        self._output_thr.join()

