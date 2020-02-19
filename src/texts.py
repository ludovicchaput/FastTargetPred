
app_header = """\
* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

      TargetPred version {}

* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
"""

abstract = """\
Predict targets from input molecules.
"""

help_files_input = "Input file(s) of the query compounds. It must be in SDF format. Can be a comma separated list of files."
help_db = """\
Database to screen (default: chembl25).
    We provide 2 databases:
        1. "chembl25" it gathers a subset of active compounds with good confidence score (see details).
        2. "approved" it gathers 1500 approved drugs taken from the ChEMBL25.
        
"""
help_fp = """\
Fingerprint(s) to use (default: ECFP4).

    Users can select between 1 and 4 fingerprints. 
    If more than 1 fingerprint are provided, consensus score is calculated.
    Example:
            -fp ECFP4                   (only use ECFP fingerprint)
            -fp ECFP4 PL MACCS          (combine ECFP, PL and MACCS fingerprint)

    List of accepted fingerprints:

        ECFP4 (radius 2)   1024 bits
        ECFP6 (radius 3)   1024 bits
        MACCS               322 bits
        PL (PathLength)    1024 bits
        
"""
help_tc = """\
Tanimoto Threshold

    Default: Tanimoto = 0.8 for FP* and 0.6 for ECFP* fingerprints
    It is the Tanimoto threshold used to filter matching compounds.
    In case  users select the consensus approach (2 fingerprints specified or more), 
    the number of fingerprints must be the same as the number of Tanimoto threshold values (and be given in the same order).
    Example:
            -tc 0.6 0.6 0.8             (Filter out hit compounds with first and second fingerprint's Tanimoto,
                                        threshold values strictly less than 0.6 for the first and second fingerprints and
                                        for the third fingerprint strictly less than 0.8)

"""
help_sd = """\
Standard deviation threshold

    Default: 0.8.
    Standard deviation threshold is calculated on the z-scores and can be used in combination with the Tanimoto threshold.
    If multiple fingerprints are used, the sd threshold applies to the consensus score.
    Example:
            -sd 2.5                     (Filter out hit compounds with less than 2.5 zscore)
    
"""
help_nbt = """\
Maximum number of targets to report. If < 1, all target will be reported.

    Default: 100
    Example:
            -npt 25                     (Keep 25 best hits)
            -npt 0                      (Keep all hits)
            -npt -1                     (Keep all hits)
    
"""
help_output = """\
Result output channel.

    Default: stdout
    Allow to choose a file for printing results.
    Example:
            -o output.txt               (output in file "output.txt" in the current directory)
"""
help_format = """\
Result output format.

    Default: txt
    Allow to choose a format file for printing results. Currently support .csv and .txt
    Example:
            -f txt                      (output in the default txt formatted file)

    List of accepted file format :
            txt
            csv

"""
help_cpu = """\
Number of CPUs used for the computations.

    Default: 4
    Allow to choose the number of CPUs used during the Tanimoto calculations. (This does not affect prior maya calculation)
    Example:
            -cpu 8                      (run Tanimoto's calculations on 8 cores)
    
"""
help_bppt = """\
Keep or not all hits for the same target from multiple database ligands.

    Default: Keep best score
    When a hit passes the threshold filtering, a verification is performed on all target hits.
    If a duplicate target is found, the hit with the best query-ligand score is kept. Other hits are discarded.
    Adding this flag allow to disable this behaviour and to see all hits. Be careful to increase the maximum 
    target number accordingly for this may increase the output size and hides other hits.
    Example:
            -bppt                       (disable best score filtering)
    
"""
help_noinfo = """\
Show or not information about target hits.

    Default: Show information
    Option to hide information about targets in the output.
    Example:
            -noinfo                       (hide information)
    
"""
system_not_ok = """\
System verification found an anomaly in your system setup. Here is some hint(s) on how to correct it :\n
"""
arg_checked = "Arguments checked."
check_system = "{:<40}".format("Checking local system ...")
check_arg = "{:<40}".format("Checking input arguments ...")
start_maya = "{:<40}".format("Starting maya calculation ...")
maya_time_estimation = "{:<40}".format("Estimated time : {:> 6}s ...")
maya_finished = "{:<40}".format("Time for maya calculation: {}")
start_tanimoto = "{:<40}".format("Starting tanimoto computation on {} cores.")
checked = 'ok'
sdf_no_mol_name_error = "Error found in input SDfile {}. Molecule number {} has no name."
sdf_mol_name_duplicate_error = "Duplicate name found in input SDFile {}: {}. Is that the same molecule ?"
sdf_checked = "Input SD file(s) checked."
merge_error = "0 molecules retrieved from provided SDFs during file merge."
molecules_found = 'A total of {} molecules has been found.'
sdf_merged = 'Input SD files merged into {}'
processing_results = "Processing results ..."
maya_error = "Maya issued an error during {} fingerprint calculation : \n{}"
file_exists = "Output file Exists. Data might be crushed. Please choose another file name."
progression_ruler = """\
Job progression percentage : 
0 %     10        20        30        40        50        60        70        80        90        100 %
+--------+---------+---------+---------+---------+---------+---------+---------+---------+---------+
"""
input_maya_path_help = "\nPath to MayaChemTools not found. Please Enter it before proceeding :\n>"
input_maya_incorrect = "\nMayaChemTools folder not recognized. Please make sure to enter the \"bin\" subfolder.\n>"

