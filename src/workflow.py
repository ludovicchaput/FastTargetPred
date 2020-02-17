# Python 3.7 Built-in packages
from time import time

# Local packages
from src.arg_parsing import UserArguments, NUM_CORE
from src.fingerprints import FingerprintList
from src.molecules import MoleculeList
from src import texts

def start():
    # Parsing the user arguments
    user_args = UserArguments.get()
    print(texts.check_arg, end='')
    error, msg = not user_args.are_ok(), user_args.errormsg
    query_dicts = []

    if not error:
        print(texts.checked)

        sdf = user_args.sdf_path  # Keeping the sdf reference here allow to change the workflow to loop on a sdf list or similar

        print(user_args.verbose_msg, end='')
        print(texts.start_maya, end='')
        print()
        print(texts.maya_time_estimation.format(user_args.number_query_molecule_found), end='')

        fps = FingerprintList(user_args, sdf)
        fps.create_fingerprints()
        t0 = time()
        query_dicts = fps.generate_molecule_files()

        print(texts.checked)
        print(texts.maya_finished.format(time() - t0))

        print(texts.start_tanimoto.format(user_args.dict[NUM_CORE]))

        molecules = MoleculeList.create_list(user_args, query_dicts, fps)
        molecules.compute_fingerprints()



    if error:
        print("Err")
        print(msg)
