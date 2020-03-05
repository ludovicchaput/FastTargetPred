# Python 3.7 Built-in packages
from pathlib import Path
import argparse

# Local packages
from . import texts
from . import config
from . import output



# Class that hold arguments
class UserArguments(object):

    @classmethod
    def get(cls):  # Get Arguments object from argument list
        o = cls(_get_args_dict())
        return o

    def __init__(self, arg_dict: dict):
        self.dict = arg_dict
        self.errormsg = ''
        self.merged_sdf = Path("target_prediction_merged_sdf.sdf")
        self._output_object = None
        self._merged_sdf: Path = None
        self.verbose_msg: str = ""
        self.number_query_molecule_found = -1

    def get_tc_threshold(self, fp_name) -> float:
        if self.dict[TANIMOTO_COEF_THRESHOLD] is config.DEFAULT_TC:
            return config.DEFAULT_TC_THRESHOLD[fp_name]
        else:
            return self.dict[TANIMOTO_COEF_THRESHOLD][self.dict[FINGERPRINT].index(fp_name)]


    def get_threshold(self, *args) -> float:
        if self.consensus:
            return self.dict[ZSCORE_THRESHOLD]
        else:
            return self.get_tc_threshold(self.dict[FINGERPRINT][0])

    @property
    def output_file(self) -> Path:
        return Path("output.txt")

    @property
    def is_output_file(self) -> bool:
        return self.dict[OUTPUT] is not config.DEFAULT_OUTPUT

    @property
    def db_path(self):
        # Using path library allow not caring about user's operating system
        return str(Path(self.dict[DATABASE]))

    @property
    def sdf_path(self):
        if self._merged_sdf is None:
            if len(self.dict[SDFile]) > 1:
                self.merge_sdf()
            else:
                self._merged_sdf = Path(self.dict[SDFile][0])
        return self._merged_sdf

    @property
    def consensus(self) -> bool:  # Figure out if there is a consensus or not
        return len(self.dict[FINGERPRINT]) > 1

    @property
    def max_target_number(self) -> int:
        return self.dict[REPORTED_TARGET_NUMBER]

    @property
    def output_function(self) -> output.OutputObject:
        if self._output_object is None:
            args = (self.dict[OUTPUT_FORMAT], self.max_target_number, self.show_info)
            if self.dict[OUTPUT] is config.DEFAULT_OUTPUT:
                self._output_object = output.OutputObject(0, *args)
            else:
                self._output_object = output.OutputObject(1, *args)
                self._output_object.file = self.dict[OUTPUT]
        return self._output_object

    @property
    def zscore_threshold(self) -> float:
        return self.dict[ZSCORE_THRESHOLD]

    @property
    def not_filter_best_match_per_target(self) -> bool:
        return self.dict[FILTER_BEST_POSE_PER_TARGET]

    @property
    def show_info(self):
        return not self.dict[NO_INFO]

    # Check user inputs
    def are_ok(self) -> bool:
        are_they = True

        i = 0
        for i in range(len(self.dict[FINGERPRINT])):
            self.dict[FINGERPRINT][i] = self.dict[FINGERPRINT][i].upper()

        for fp in self.dict[FINGERPRINT]:
            if fp not in config.FP_AVAILABLE:
                are_they = False
                self.errormsg += f"Fingerprint {fp} not available.\n"

        for sdf in self.dict[SDFile]:
            sdf_path = Path(sdf)
            if not sdf_path.is_file() and sdf_path.suffix == "sdf":
                are_they = False
                self.errormsg += f"File {sdf} not found.\n"

        # if self.dict[REPORTED_TARGET_NUMBER] < 1:
        #     are_they = False
        #     self.errormsg += f"Number of reported target must be more than 1.\n"

        if self.dict[TANIMOTO_COEF_THRESHOLD] is not config.DEFAULT_TC:
            for tc in self.dict[TANIMOTO_COEF_THRESHOLD]:
                if tc < 0 or tc > 1:
                    are_they = False
                    self.errormsg += f"Tanimoto coefficient value must be between 0 and 1.\n"

            if len(self.dict[TANIMOTO_COEF_THRESHOLD]) != len(self.dict[FINGERPRINT]):
                are_they = False
                self.errormsg += f"Fingerprint number and Tanimoto threshold mismatch.\n"

        if not Path(self.dict[DATABASE] + config.DEFAULT_TLT_FILE_SUFFIX).is_file():
            are_they = False
            self.errormsg += f"Database {self.dict[DATABASE]} not found.\n"

        if self.dict[OUTPUT] is not config.DEFAULT_OUTPUT:
            if not Path(self.dict[OUTPUT]).parent.is_dir():
                are_they = False
                self.errormsg += f"Directory {Path(self.dict[OUTPUT]).parent} not found.\n"
            if Path(self.dict[OUTPUT]).is_file():
                are_they = False
                self.errormsg += f"File {Path(self.dict[OUTPUT])} Already exists. It may cause data loss.\n"

        if self.dict[OUTPUT_FORMAT] not in config.AVAILABLE_FILE_FORMAT:
            are_they = False
            self.errormsg += f"File format {Path(self.dict[OUTPUT_FORMAT])} not supported. Supported format are : {','.join(config.AVAILABLE_FILE_FORMAT)}.\n"

        if self.check_sdf() is False:
            are_they = False

        if not are_they:
            self.errormsg = "Error found in arguments :\n" + self.errormsg

        return are_they

    def check_sdf(self) -> (bool, str):
        """
        Check if the input SDfile have all uniquely named molecules.
        """
        error = False
        msg = ""

        mol_name_list = []  # For duplicate name finding purpose

        for file in self.dict[SDFile]:
            with open(file, "r", encoding=config.ENCODING) as f:
                sdf_str = f.read()

            mols_sdf_str = sdf_str.split(config.SD_MOL_DELIMITER)

            i = 1
            for mol_sdf_str in [m for m in mols_sdf_str if m != ""]:
                if mol_sdf_str[0] == '\n':  # if the first character is line feed, it mean that the name is empty
                    error = True
                    msg += texts.sdf_no_mol_name_error.format(file, i)
                else:
                    # Taking the molecule's name
                    i = 0
                    c = mol_sdf_str[0]
                    mol_name = ''
                    while c != '\n':
                        mol_name += c
                        i += 1
                        c = mol_sdf_str[i]

                    if mol_name in mol_name_list:  # Check if the name already appeared before
                        error = True
                        msg += texts.sdf_mol_name_duplicate_error.format(file, mol_name)
                    else:
                        mol_name_list.append(mol_name)
        self.number_query_molecule_found = len(mol_name_list)
        self.verbose_msg = texts.molecules_found.format(self.number_query_molecule_found) + "\n"
        self.errormsg += msg
        return not error


    def merge_sdf(self) -> (bool, str):
        # Merge all user provided sd files
        sd_mol_delimiter = config.SD_MOL_DELIMITER
        mol_list = []
        for sdf in self.dict[SDFile]:
            # append all molecules from the file into the molecule list (if the molecule is not empty)
            mol_list.extend([m for m in Path(sdf).read_text(encoding=config.ENCODING).split(sd_mol_delimiter) if len(m) > 0])

        if len(mol_list) == 0:
            self.errormsg += texts.merge_error
            raise RuntimeError(self.errormsg)

        self._merged_sdf = Path(config.DEFAULT_MERGE_SDF_NAME)
        self._merged_sdf.write_text(sd_mol_delimiter.join(mol_list), encoding=config.ENCODING)



# These are modes for asking threshold (asking for TANIMOTO threshold or ZSCORE threshold
TANIMOTO = 0
ZSCORE = 1

# Var that hold arguments for user to alter program behaviour.
# Also used by the program to access arguments value as dictionnary key
SDFile = 'SDFile'
DATABASE = 'db'
FINGERPRINT = 'fp'
TANIMOTO_COEF_THRESHOLD = 'tc'
ZSCORE_THRESHOLD = 'sd'
REPORTED_TARGET_NUMBER = 'nbt'
OUTPUT = 'o'
OUTPUT_FORMAT = 'f'
NUM_CORE = 'cpu'
FILTER_BEST_POSE_PER_TARGET = 'bppt'
NO_INFO = 'noinfo'

ARGS_LIST = [
    SDFile
    , DATABASE
    , FINGERPRINT
    , TANIMOTO_COEF_THRESHOLD
    , ZSCORE_THRESHOLD
    , REPORTED_TARGET_NUMBER
    , OUTPUT
    , OUTPUT_FORMAT
    , NUM_CORE
    , FILTER_BEST_POSE_PER_TARGET
    , NO_INFO
]



def _get_args_dict() -> dict:
    parser = _get_argparse_setup()

    # Get arparse namespace
    ns = parser.parse_args()

    # Return arguments in a dictionary fashion
    d = {a: ns.__getattribute__(a) for a in ARGS_LIST}
    return d


# Initialize the argument parser for later use.
def _get_argparse_setup() -> argparse.ArgumentParser:
    # the formatter_class here allow to the help string to be formatted as it is in the texts.py
    parser = argparse.ArgumentParser(description=texts.abstract
                                     , formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(SDFile, metavar="SDF", type=str, nargs="+"
                        , help=texts.help_files_input)
    # parser.add_argument(f'-i', dest=SDFile, type=str, nargs="+", default=""
    #                     , help=texts.help_files_input)
    parser.add_argument(f'-{DATABASE}', dest=DATABASE, type=str, default=config.DEFAULT_DB
                        , help=texts.help_db)
    parser.add_argument(f'-{FINGERPRINT}', dest=FINGERPRINT, type=str, nargs='+', default=[config.DEFAULT_FP]
                        , help=texts.help_fp)
    parser.add_argument(f'-{TANIMOTO_COEF_THRESHOLD}', dest=TANIMOTO_COEF_THRESHOLD, type=float, nargs="+", default=config.DEFAULT_TC
                        , help=texts.help_tc)
    parser.add_argument(f'-{ZSCORE_THRESHOLD}', dest=ZSCORE_THRESHOLD, type=float, default=config.DEFAULT_SD
                        , help=texts.help_sd)
    parser.add_argument(f'-{REPORTED_TARGET_NUMBER}', dest=REPORTED_TARGET_NUMBER, type=int, default=config.DEFAULT_NBT
                        , help=texts.help_nbt)
    parser.add_argument(f'-{OUTPUT}', dest=OUTPUT, type=str, default=config.DEFAULT_OUTPUT
                        , help=texts.help_output)
    parser.add_argument(f'-{OUTPUT_FORMAT}', dest=OUTPUT_FORMAT, type=str, default=config.DEFAULT_OUTPUT_FORMAT
                        , help=texts.help_format)
    parser.add_argument(f'-{NUM_CORE}', dest=NUM_CORE, type=int, default=config.DEFAULT_NUM_CORE
                        , help=texts.help_cpu)
    parser.add_argument(f'-{FILTER_BEST_POSE_PER_TARGET}', dest=FILTER_BEST_POSE_PER_TARGET, action="store_true"
                        , help=texts.help_bppt)
    parser.add_argument(f'-{NO_INFO}', dest=NO_INFO, action="store_true"
                        , help=texts.help_noinfo)
    return parser



