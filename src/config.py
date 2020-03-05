# Python 3.7 Built-in packages
import typing
from sys import argv
from pathlib import Path

BASE_PATH = str(Path(argv[0]).resolve().parent)
                                        # Retrieve App install folder
BASE_TEMP_DIR = BASE_PATH + "/" + "temp"
                                        # Default database path
DEFAULT_DB = BASE_PATH + '/' + "db/chembl25_active"
DEFAULT_FP = "ECFP4"                    # Default fingerprint used
DEFAULT_SD = 0.8                        # Default Zscore threshold for hit filtering
DEFAULT_NBT = 100                       # Default target number displayed
DEFAULT_NUM_CORE = 4
DEFAULT_OUTPUT_FORMAT = "txt"
CSV_FILE_FORMAT = "csv"
DEFAULT_CSV_DELIMITER = "\t"
DEFAULT_MERGE_SDF_NAME = "out/target_prediction_merged_sdf.sdf"
DEFAULT_BINARY_FINGERPRINT_FOLDER = BASE_TEMP_DIR + '/' + "binary_fingerprints"
                                        # Default Name of merged sdf

DEFAULT_TID_CHEMBLID_FILE_NAME = BASE_PATH + '/' + "db/tid-chembl_lookuptable.csv"
                                        # Default name of the file that link tid to CHEMBLID

TID_CHEMBLID_DELIMITER = ","            # Delimiter of the csv file
CORR_TID_FIELD_NAME = 'tid'
CORR_CHEMBLID_FIELD_NAME = 'chembl_id'
SAVED_MAYA_PATH_FILE = BASE_PATH + '/' + "src/maya_path"

DEFAULT_UNIPROT_DATABASE__CHEMBL_FILE_NAME = BASE_PATH + '/' + "db/uniprot_database_ChEMBL.csv"
                                        # Default name of the file that give some informations about TID
DEFAULT_TLT_FILE_SUFFIX = ".tlt"

UNIPROT_DATABASE__CHEMBL_FILE_DELIMITER = '\t'
                                        # Delimiter of the csv file
INFO_CHEMBLID_FIELD_NAME = 'CHEMBL'
INFO_UNIPROTID_FIELD_NAME = 'Uniprot'

ENCODING = 'utf-8'                      # encoding of red files

PROGRESSION_SYMBOL = "#"

DEFAULT_TC_THRESHOLD = {                # Default threshold that will be applied if no threshold are specified.
    "ECFP4": 0.6                        #  Note that in case of consensus, both fingerprint threshold and zscore
    , "ECFP6": 0.6                      #  threshold will be applied.
    , "MACCS": 0.8
    , "PL": 0.7
}

# From here, values should not be changed

FINGERPRINT_CMD = {                     # Oh my god don't ever touch that unless you know what you're doing.
    "ECFP4": ["ExtendedConnectivityFingerprints.pl", "-m ExtendedConnectivityBits -n 2"]
    , "ECFP6": ["ExtendedConnectivityFingerprints.pl", "-m ExtendedConnectivityBits -n 3"]
    , "MACCS": ["MACCSKeysFingerprints.pl", "-s 322 -b HexadecimalString"]
    , "PL": ["PathLengthFingerprints.pl", "-m PathLengthBits -b HexadecimalString"]
}
FINGERPRINT_SIZE = {                    # Same here. Please don't.
    "ECFP4": 1024
    , "ECFP6": 1024
    , "MACCS": 328
    , "PL": 1024
}

AVAILABLE_FILE_FORMAT = [
    DEFAULT_OUTPUT_FORMAT
    , CSV_FILE_FORMAT
]

SD_MOL_DELIMITER = "\n$$$$\n"           # SDfiles molecule delimiter
DEFAULT_TC = object()                   # Sentry for mem adress checking
DEFAULT_OUTPUT = object()               # Sentry for mem adress checking

FP_AVAILABLE = FINGERPRINT_CMD.keys()   # Will hold the list of available fingerprint. Used while checking arguments.

Target_Id = typing.NewType("Target_Id", str)
Database_Id = typing.NewType("Database_Id", str)
Score = typing.NewType("Score", float)

