# Python 3.7 Built-in packages
import typing
import gc
import multiprocessing as mp
import threading
import math

# Local packages
from src.molecule import Molecule
from src.progression_bar import ProgressionBar
from .fingerprints import FingerprintList
from .arg_parsing import UserArguments, NUM_CORE


class MoleculeList(object):
    @classmethod
    def create_list(cls, args: UserArguments, query_dicts: typing.List[typing.Dict[int, typing.Any]], fps: FingerprintList):
        o = cls(args, query_dicts, fps)
        o._create_list(fps)
        return o

    def _create_list(self, fps: FingerprintList): # Create the list of molecule object that will hold computations
        max_target = self.user_arguments.max_target_number
        best_match_per_target = self.user_arguments.not_filter_best_match_per_target
        self._db_thr.start()
        self._info_thr.start()
        for query_dict in self.query_dicts:
            self.molecules.append(Molecule(query_dict, max_target, best_match_per_target))

    def __init__(self, args: UserArguments, query_dicts:  typing.List[typing.Dict[int, typing.Any]], fps: FingerprintList):
        self.user_arguments: UserArguments = args
        self.molecules: typing.List[Molecule] = []
        self.query_dicts:  typing.List[typing.Dict[int, typing.Any]] = query_dicts

        self.processes_manager = mp.Manager()
        self.output_lock = self.processes_manager.Lock()

        self.db_lock = self.processes_manager.Lock()
        self.db_lock.acquire()

        self.info_lock = self.processes_manager.Lock()
        self.info_lock.acquire()

        self.shared_db = self.processes_manager.dict()
        self.shared_info = self.processes_manager.dict()
        self._db_thr = threading.Thread(
            target=self._share_db
            , args=(fps.get_db, )
        )
        self._info_thr = threading.Thread(
            target=self._share_info
            , args=(fps.get_info, )
        )
        self.shared_progression_queue = self.processes_manager.Queue()
        self.shared_output_queue = self.processes_manager.Queue()
        self.compute_arguments = ((self.db_lock, self.shared_db),)

    def _share_db(self, get_db: callable):
        self.shared_db.update(get_db())
        self.db_lock.release()

    def _share_info(self, get_info: callable):
        self.shared_info.update(get_info())
        self.info_lock.release()

    def compute_fingerprints(self):
        num_concurrent_processes = self.user_arguments.dict[NUM_CORE]
        processes = []  # We keep a list of processes to join them
        molecules_number = len(self.molecules)
        molecule_per_process = max(math.floor(molecules_number / num_concurrent_processes), 1) # Number of molecule per process
        molecules_list = []  # Will hold a list of list of molecules to distribute calculations among a specified number of cores

        while len(self.molecules) > 0:
            molecules = []
            for f in range(molecule_per_process):
                if len(self.molecules) == 0:
                    break
                molecules.append(self.molecules.pop(0))
            molecules_list.append(molecules)

        i = 0  # Just for process naming purpose
        for molecules in molecules_list:
            # Start the right number of processes
            process = mp.Process(
                    target=compute_molecule_list
                    , args=(self.compute_arguments, molecules, self.shared_progression_queue, self.shared_output_queue)
                    , name="tanimoto_process_{}".format(i)
                )
            process.start()
            processes.append(process)
            i += 1

        if self.user_arguments.is_output_file:
            progression_bar = ProgressionBar(molecules_number, self.shared_progression_queue)
            progression_bar.initialize()
            progression_bar.watch_progression()

        output_object = self.user_arguments.output_function
        output_object.watch_output(self.shared_info, self.shared_output_queue, molecules_number)

        [p.join() for p in processes]  # Join all processes
        output_object.wait()
        print()


def compute_molecule_list(compute_arguments, molecules: typing.List[Molecule], shared_progression_queue, shared_output_queue):
    gc.disable()  # Disable automated garbage collector while computing. Great performance improve
    for molecule in molecules:
        molecule.compute_tanimoto(*compute_arguments, shared_progression_queue, shared_output_queue)
        gc.collect()  # Clean unreferenced variables manually to avoid memory overflow
    gc.enable()  # Re-enable garbage collector back.


