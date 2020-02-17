# Python 3.7 Built-in packages
import typing
from dataclasses import dataclass

# Local packages
from .fingerprints import MOLECULE_NAME, QBFP_FILE, TC_PROCESS_ARGS
from .config import Target_Id, Database_Id, Score
from .misc import is_windows, is_mac, is_linux

# Import the compiled C library. This complex import is made to be plateform-independant.
try:
    if is_windows():
        from .clib_w64.tanimoto_processing import tc_process
    elif is_linux():
        from .clib_linux64.tanimoto_processing import tc_process
    elif is_mac():
        from .clib_mac64.tanimoto_processing import tc_process
except ImportError:
    print("Error during compiled library importation. If the problem persists, please re-install the application.")
    exit(1)


class Molecule(object):
    def __init__(self, query_dict: typing.Dict[int, typing.Any],  max_target: int, not_filter_best_match_per_target: bool):
        self.name = query_dict[MOLECULE_NAME]
        self.bfp_file = query_dict[QBFP_FILE]
        self.tc_process_args = query_dict[TC_PROCESS_ARGS]
        self.hits: typing.List[Hit] = []
        self.max_target_number: int = max_target
        self.hit_results_dict: typing.Dict[Target_Id, typing.List[typing.Tuple[Database_Id, Score]]] = {}
        self.not_filter_best_match_per_target = not_filter_best_match_per_target

    def compute_tanimoto(self, shared_db, shared_progression_queue, output_queue):  # Compute tanimoto, zscore if asked then give results

        # Start C module. current bottleneck (with maya of course)
        results_dict: typing.Dict[Database_Id, typing.List[Score]] = tc_process(*self.tc_process_args)
        # print(f"Molecule : {self.name} - End of C computation - {len(results_dict.keys())} hits found\n", end='')
        shared_db[0].acquire()  # I'm not sure it is usefull to lock dictionary while reading
        db = shared_db[1]
        for k, v in results_dict.items():
            self.hits.append(Hit(k, db.get(k, []), v[-1]))
        shared_db[0].release()
        self.compute_bmpt()

        shared_progression_queue.put(None)
        output_queue.put((self.hit_results_dict, self.name))

        # Adding None to the queue allow main process to know when this molecule's job's is finished

    def compute_bmpt(self):  # Build the best match per target dictionary (based on the higher zscore)
        d = {}
        n_hits = 0
        for hit in self.hits:
            t_dict: typing.Dict[Target_Id, typing.Tuple[Database_Id, Score]] = hit.target_dict
            for k, v in t_dict.items():
                n_hits += 1
                if k not in d:  # If no hit with this name, simply add the result.
                    d[k] = [v]
                else:  # Compare zscore of result already in dict versus the current zscore from loop
                    v_list = d[k]
                    if self.not_filter_best_match_per_target:
                        v_list.append(v)
                    elif v_list[0][1] < v[1]:
                        v_list[0] = v

        # print(f"Molecule : {self.name} - {n_hits} hits found\n", end='')
        self.hit_results_dict = d


@dataclass
class Hit(object):  # Hold db name of a molecule that is beneath the thresholds
    chembl_id:     str
    targets:       typing.List[str]
    score:         float

    @property
    def target_dict(self) -> typing.Dict[Target_Id, typing.Tuple[Database_Id, Score]]:  # Rearrange data so strings can be generated easily
        return {t: (self.chembl_id, self.score) for t in self.targets}
