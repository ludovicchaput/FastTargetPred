# Python 3.7 Built-in packages
import typing
import codecs
import csv
from pathlib import Path
import threading

# Local packages
from . import config
from .fingerprint import Fingerprint
from .arg_parsing import UserArguments, FINGERPRINT, SDFile

MOLECULE_NAME = 0
QBFP_FILE = 1
TC_PROCESS_ARGS = 3


def get_empty_tc_process_dict():
    return {
        MOLECULE_NAME: None
        , QBFP_FILE: None
        , TC_PROCESS_ARGS: None
    }


class FingerprintList(object):
    def __init__(self, args: UserArguments, sdf: Path):
        self.user_arguments: UserArguments = args
        self.fp_list: typing.List[Fingerprint] = []
        self.molecule_files = []
        self.sdf: Path = sdf

        # DB reading thread
        self._info_thread = threading.Thread(
            target=self._read_info
            , name='thread_read_info'
        )
        self._info_dict: typing.Dict[str, typing.List[str]] = {}
        self._db_thread = threading.Thread(
            target=self._read_database
            , name='thread_read_db'
        )
        self._db: typing.Dict[str, typing.List[str]] = {}

        temp_dir_path = Path(config.DEFAULT_BINARY_FINGERPRINT_FOLDER)
        if not temp_dir_path.is_dir():
            temp_dir_path.mkdir()
        self.bfp_dir: Path = temp_dir_path
        self.bfp_files: typing.List[typing.Tuple[str, Path]] = []
        self.db_list: typing.List[str] = []
        self.tc_threshold_list: typing.List[float] = []
        self.query_dicts: typing.List[dict] = []

    def create_fingerprints(self):
        for fp_name in self.user_arguments.dict[FINGERPRINT]:
            self.fp_list.append(Fingerprint(fp_name, self.user_arguments, self.sdf))

    def generate_molecule_files(self) -> typing.List[typing.Dict[int, typing.Any]]:  # Start maya calculation in parallel (Worth it)
        # Start maya calculation
        for fp in self.fp_list:
            fp.start_maya_calculation()

        # Start reading target database and info for future matching
        self._db_thread.start()
        self._info_thread.start()

        self.db_list = [fp.db_bytes for fp in self.fp_list]
        # self.db_list = [fp.db_name for fp in self.fp_list]
        self.tc_threshold_list = [fp.threshold for fp in self.fp_list]

        self.assemble_files([fpf for fpf in [(fp.fp_files[0], fp.length, fp.name) for fp in self.fp_list]])

        return self.query_dicts

    def assemble_files(self, fpf_list: typing.List[typing.Tuple[Path, int, str]]):
        d: typing.Dict[str, typing.List[typing.Tuple[bytes, bytes]]] = {}

        for fpf, fp_length, fp_name in fpf_list:

            lines: typing.List[str] = fpf.read_text(encoding=config.ENCODING).split('\n')[:-1]
            while lines[0][0] == '#':
                lines.pop(0)

            for molecule_name, v in [line.split(' ') for line in lines]:

                fp_length_bytes = fp_length.to_bytes(4, byteorder='big', signed=False)
                if molecule_name not in d:
                    d[molecule_name] = [(codecs.decode(v, 'hex'), fp_length_bytes)]
                else:
                    d[molecule_name].append((codecs.decode(v, 'hex'), fp_length_bytes))

        if not self.bfp_dir.is_dir():
            self.bfp_dir.mkdir()

        static_arguments = (self.db_list, self.tc_threshold_list, self.user_arguments.zscore_threshold, self.user_arguments.consensus)

        for molecule_name, bfps in d.items():
            query_dict = get_empty_tc_process_dict()
            query_dict[MOLECULE_NAME] = molecule_name

            file = Path(self.bfp_dir, "{}.qbfp".format(molecule_name))
            stream = file.open('wb')

            query_dict[QBFP_FILE] = file
            query_dict[TC_PROCESS_ARGS] = ("{}".format(file), *static_arguments)


            molecule_name_length = len(molecule_name).to_bytes(1, byteorder='big', signed=True)
            encoded_molecule_name = molecule_name.encode('ascii')
            for bfp, fp_length_byte in bfps:
                stream.write(molecule_name_length)
                stream.write(encoded_molecule_name)
                stream.write(fp_length_byte)
                stream.write(bfp)
            stream.close()

            self.query_dicts.append(query_dict)
            self.bfp_files.append((molecule_name, file))

    def _read_database(self):
        text_ = Path(self.user_arguments.db_path + '_all.tlt').read_text()
        self._db = {l[0]: l[1:] for l in [line.split(' ') for line in text_.split('\n')]}

    def _read_info(self):

        # Create filter function for info dictionary generation
        def info_to_be_filtered(k):
            return True
        if not self.user_arguments.show_info:
            def info_to_be_filtered(key):
                # Filter out key that are not uniprot id nor chemblid
                return key == config.INFO_UNIPROTID_FIELD_NAME \
                       or key == config.INFO_CHEMBLID_FIELD_NAME

        def get_correlation_dict(file_name: str) -> typing.Dict[str, str]:
            # Give dict that take the TID as key and return chembl_id
            file = Path(file_name).open('r', encoding=config.ENCODING)
            od = csv.DictReader(file, delimiter=config.TID_CHEMBLID_DELIMITER)
            d = {f[config.CORR_TID_FIELD_NAME]: f[config.CORR_CHEMBLID_FIELD_NAME] for f in od}
            file.close()
            return d

        def get_info_dict(file_name: str) -> typing.Dict[str, typing.List[typing.Dict[str, str]]]:
            # Give a dict that take the CHEMBLID as key and return a dict of information
            file = Path(file_name).open('r', encoding=config.ENCODING)
            od = csv.DictReader(file, delimiter=config.UNIPROT_DATABASE__CHEMBL_FILE_DELIMITER)
            normal_dict_list = [{k: v for k, v in d.items() if info_to_be_filtered(k)} for d in od]
            return_d = {normal_dict[config.INFO_CHEMBLID_FIELD_NAME]: [] for normal_dict in normal_dict_list}
            [return_d[normal_dict[config.INFO_CHEMBLID_FIELD_NAME]].append(normal_dict) for normal_dict in normal_dict_list]
            file.close()
            return return_d

        # correl_dict = get_correlation_dict(config.DEFAULT_TID_CHEMBLID_FILE_NAME)
        # info_dict = get_info_dict(config.DEFAULT_UNIPROT_DATABASE__CHEMBL_FILE_NAME)
        self._info_dict = get_info_dict(config.DEFAULT_UNIPROT_DATABASE__CHEMBL_FILE_NAME)
        # print(self._info_dict)
        # correl_dict = get_correlation_dict(config.DEFAULT_TID_CHEMBLID_FILE_NAME)
        # info_dict = get_info_dict(config.DEFAULT_UNIPROT_DATABASE__CHEMBL_FILE_NAME)
        # self._info_dict = {k: info_dict[v] for k, v in correl_dict.items() if v in info_dict}

        # l = []  # Some lines I decided to keep to check file reading if changes occur
        # [[l.append(vv) for vv in v] for v in self._info_dict.values()]
        # print(f"Length of the information dictionary: {len(l)}")

    def get_info(self) -> typing.Dict[str, typing.List[str]]:
        self._info_thread.join()
        return self._info_dict

    def get_db(self) -> typing.Dict[str, typing.List[str]]:
        self._db_thread.join()
        return self._db

