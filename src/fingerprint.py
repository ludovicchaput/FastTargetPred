# Python 3.7 Built-in packages
import subprocess
import threading
from pathlib import Path

# Local packages
from . import config
from . import texts
from .arg_parsing import UserArguments
from .misc import get_perl_path, get_maya_path

class Fingerprint(object):
    perl_path = get_perl_path()


    def __init__(self, name: str, args: UserArguments, sdf: Path):
        self.maya_path = get_maya_path()
        self.name = name  # refer to the fingerprint reference
        self.user_arguments = args
        self.fingerprint_size = config.FINGERPRINT_SIZE[name]

        self._maya_thread = threading.Thread(
            name=f"maya_{name}"
            , target=self.maya_fp_calculation
            , args=(sdf,)
        )
        self._db_thread = threading.Thread(
            name=f"db_{name}"
            , target=self._read_db_bytes
        )

        # All lists that will be filled along the calculation
        self._db_bytes: bytes = bytes()
        self._fp_files = []
        self.bfp_files_name = []
        self.compound_list = []
        self.out_files_name = []

        # Results
        self._results_array = []
        self._results_dict = {}
        self._db = {}

        self.error = False
        self.errormsg = ''

    def start_maya_calculation(self):
        self._db_thread.start()
        self._maya_thread.start()

    @property
    def fp_files(self):
        self._maya_thread.join()
        return self._fp_files

    @property
    def length(self) -> int:
        return config.FINGERPRINT_SIZE[self.name]

    @property
    def threshold(self) -> float:
        return self.user_arguments.get_tc_threshold(self.name)

    @property
    def db_name(self) -> str:
        return "{}_{}.bfp".format(self.user_arguments.db_path, self.name)

    @property
    def db_bytes(self) -> bytes:
        self._db_thread.join()
        return self._db_bytes

    def _read_db_bytes(self):
        self._db_bytes = Path("{}_{}.bfp".format(self.user_arguments.db_path, self.name)).read_bytes()



    # start the maya calculation for this fingerprint
    def maya_fp_calculation(self, sdf_filename: str):
        """
        It seems maya sdf reading doesn't lock the file, unlike C's fread.
        So it might be useless to make [fp_number] sdf replicates for each maya thread.
        """
        base_sdf = Path(sdf_filename)
        # sdf = Path(f'{self.name}_tmp.sdf')
        # sdf.write_text(base_sdf.read_text(encoding=config.ENCODING), encoding=config.ENCODING)
        output_dir = Path("out")
        if not output_dir.is_dir():
            output_dir.mkdir()

        fp_files_name = Path( f"{base_sdf.stem}_{self.name}.fpf")
        shell_cmd = "{perl_path} {maya_path} {fp_cmd} --output FP --CompoundIDMode MolName -r {fp_file_name} -o {input_file}".format(
            perl_path=self.perl_path
            , maya_path=Path(self.maya_path, config.FINGERPRINT_CMD[self.name][0])
            , fp_cmd=config.FINGERPRINT_CMD[self.name][1]
            , input_file=base_sdf
            , fp_file_name=fp_files_name.stem
        )

        # Calling maya fingerprint generation
        completed_process = subprocess.run(shell_cmd, shell=True, capture_output=True, encoding=config.ENCODING)
        # sdf.unlink()

        if completed_process.returncode == 0:  # if everything went fine

            # Log maya output
            Path(output_dir, f"log_{self.name}.log").write_text(completed_process.stdout, encoding=config.ENCODING)

            # Move output in out dir
            output_file_path = Path(output_dir, fp_files_name)
            if output_file_path.is_file():
                output_file_path.unlink()
            fp_files_name.rename(output_file_path)

            self._fp_files.append(output_file_path)

        else:  # if something went wrong
            self.errormsg = texts.maya_error.format(
                self.name
                , completed_process.stderr
            )
            self.error = True
