#define PY_SSIZE_T_CLEAN
#include "Python.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "tanimoto_processing.h"

//define the size of the int containing the fingerprint length
#define FP_LENGTH_SIZE	4

// Declaring python link stuff
static PyObject *TanimotoProcessingError;
static PyMethodDef TanimotoProcessingMethods[] = {
    {"tc_process",  tc_process, METH_VARARGS, "Process binary Fingerprints with db."}
    , {NULL, NULL, 0, NULL}        /* Sentinel */
};
static struct PyModuleDef tanimoto_processing__module = {
    PyModuleDef_HEAD_INIT,
    "tanimoto_processing",   /* name of module */
    "Read qbfp file and compare each fingerprint to each molecule in the provided database bytes from bfp database file.", /* module documentation */
    -1,       /* size of per-interpreter state of the module,
                 or -1 if the module keeps state in global variables. */
    TanimotoProcessingMethods
};

PyObject* PyInit_tanimoto_processing(void) {
    PyObject *m;

    m = PyModule_Create(&tanimoto_processing__module);
    if (m == NULL)
        return NULL;

    TanimotoProcessingError = PyErr_NewException("tanimoto_processing.error", NULL, NULL);
    Py_XINCREF(TanimotoProcessingError);
    if (PyModule_AddObject(m, "error", TanimotoProcessingError) < 0) {
        Py_XDECREF(TanimotoProcessingError);
        Py_CLEAR(TanimotoProcessingError);
        Py_DECREF(m);
        return NULL;
    }

    return m;
}




/* This assumes that 'unsigned int' is 32 bits */
int popcount(unsigned int x) {
	// lookup table for counting 1s bits
	const int _popcount_counts[] = {
		0,1,1,2,1,2,2,3,1,2,2,3,2,3,3,4,1,2,2,3,2,3,3,4,2,3,3,4,3,4,4,5,
		1,2,2,3,2,3,3,4,2,3,3,4,3,4,4,5,2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6,
		1,2,2,3,2,3,3,4,2,3,3,4,3,4,4,5,2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6,
		2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6,3,4,4,5,4,5,5,6,4,5,5,6,5,6,6,7,
		1,2,2,3,2,3,3,4,2,3,3,4,3,4,4,5,2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6,
		2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6,3,4,4,5,4,5,5,6,4,5,5,6,5,6,6,7,
		2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6,3,4,4,5,4,5,5,6,4,5,5,6,5,6,6,7,
		3,4,4,5,4,5,5,6,4,5,5,6,5,6,6,7,4,5,5,6,5,6,6,7,5,6,6,7,6,7,7,8,
	};
	return (_popcount_counts[x       & 0xff]
//+
//          _popcount_counts[x >>  8 & 0xff] +
//          _popcount_counts[x >> 16 & 0xff] +
//          _popcount_counts[x >> 24 & 0xff]
);
}

// Delete keys present in the list from dictionnary if exists
void delete_keys_from_dict(PyObject* dict, PyObject* keylist) {
	Py_ssize_t t = 0; // increment var
	Py_ssize_t l = PyList_Size(keylist);
	PyObject* current_key;
	while (t<l) {
		current_key = PyList_GetItem(keylist, t);
		if (PyDict_Contains(dict, current_key)) {			
			PyDict_DelItem(
				dict
				, current_key
			);
		}
		
		t += 1;
	}
}

// Args : 
// 	query_file_name 		- name of the file that contain fingerprints of the molecule
//	database_file_name_list	- list of name of the database file to look at
//	tc_threshold_list		- list of threshold for tc filtering
//	zscore_threshold		- threshold for zscore filtering
PyObject *tc_process(PyObject *self, PyObject *args)
{
	// const char **query_file_name = PyMem_RawMalloc(sizeof(char*));
	const char *query_file_name;
	PyObject* database_file_name_list; // Must be in the same order of appearance that the molecule's fingerprint file 
	PyObject* tc_threshold_list; // Must be in the same order of appearance that the molecule's fingerprint file 
	double zscore_threshold;
	int normalize;
	
	// Argument parsing
	if(!PyArg_ParseTuple(args
			, "sOOdp"
			, &query_file_name
			, &database_file_name_list
			, &tc_threshold_list
			, &zscore_threshold
			, &normalize
		)
	){
		PyErr_SetString(TanimotoProcessingError, "Unable to read arguments.");
		return NULL;
	}
	if (!PyList_Check(database_file_name_list)){
		PyErr_SetString(TanimotoProcessingError, "Database files must be contained in a list.");
		return NULL;		
	}
	if (!PyList_Check(tc_threshold_list)){
		PyErr_SetString(TanimotoProcessingError, "Tanimoto threshold value must be contained in a list.");
		return NULL;		
	}
	
	// Evaluate filtering task
	int is_tc_threshold, is_zscore_threshold;
	if (PyList_Size(tc_threshold_list) == 0) {is_tc_threshold = 0;}else{is_tc_threshold = 1;}
	if (zscore_threshold == 0) {is_zscore_threshold = 0;}else{is_zscore_threshold = 1;}
	
	
	unsigned char query_fp[128]; // buffer that accept 128 bytes (fingerprint's size)
	unsigned char chembl_mol[128]; // buffer that accept 128 bytes (fingerprint's size)
	unsigned char* db_bytes; // Will hold the entire db bytes while looping
	Py_ssize_t db_size // Will hold the size of the db red while looping
		, db_position // Will hold the position of the 'cursor' while parsing the db
		;
	unsigned int db_id_size = 0
		, reading_i=0
		;
	
	unsigned char id_query_length[1]; // will hold query molecule's name's length over the loops
	int id_query_length_int = 0; // numerical value of the var above
	char fingerprint_length_str[FP_LENGTH_SIZE]; // will hold query molecule's fingerprint's length over the loops
	unsigned int fingerprint_length_int=0, fingerprint_byte_length_int; // numerical value of the var above
	Py_ssize_t fingerprint_number=0;
	
	unsigned int lenid_chembl_mol_int = 0;

	char id_query[255];
	char id_chembl_mol[255];

	int A, B, c;


	FILE *query_file;

	unsigned char a[1];
	a[0] = '2';
	int b = (int)a[0]; 
	unsigned int molecule_hit_count, inner_array_size=1;
	
	// vars meant to be appended to the list 
	PyObject* db_molecule_id;
	PyObject* tanimoto_score;
	PyObject* result_row;
	// Meant to hold the results of this program
	PyObject* molecule_results_list; // Hold a list of row results for current loop
	PyObject* return_dict;
	
	// Some utility vars
	PyObject* db_tanimoto_dict = PyDict_New();
	PyObject* db_zscore_dict = PyDict_New();
	PyObject* current_array_0; // will held the current python array of chemblid, tc, zscore while looping
	PyObject* current_array_1; 
	PyObject* key_2_remove_list; // will hold the keys to remove while looping on dictionnary
	PyObject *pylong_buffer_0, *pyfloat_buffer;
	PyObject *key, *value;
	double tanimoto
		, tc_sum // Will hold the sum of tanimoto's scores per molecule for standart deviation calculation
		, squared_tc_sum // Will hold the sum of the squared tanimoto's scores per molecule for standart deviation calculation
		, tc_mean_distance_sum
		, tc_stdev_loop // Will hold the tc during the stdev loop
		, tc_stdev
		, double_loop // Will hold double value during remove-key loops
		, tc_mean 
		, zscore // Will hold the zscore during zscore calculation loop
		, zscore_sum // Will hold the zscore during zscore mean calculation loop
		, zscore_mean 
		, molecule_hit_count_double
		;
	Py_ssize_t pos = 0
		, py_index=0 // Pythonized index
		;
	Py_ssize_t i, ii, l, current_array_size_int
		, remove_value // BOOL - say if we remove the value for threshold trespassing
		;
	unsigned int k=0;
	Py_ssize_t 
		db_id_index = 0
		, tc_index = 1
		, zscore_index = 2
		;
		
	int TEMP_i = 0;
		
	if (normalize) {
		inner_array_size = 3;
	} else {
		inner_array_size = 2;
	}
	query_file = fopen(query_file_name,"rb");
	
	// Loop over query molecule's fingerprint (var fingerprint_number will hold the iteration number)
	while(
		fread(id_query_length,sizeof(id_query_length),1,query_file) > 0 // read the first byte to get the size of the molecule's name
	) {
		// Figure out the length of the molecule name
		id_query_length_int = (int)id_query_length[0];
		
		// Read the molecule name
		fread(id_query,id_query_length_int,1,query_file);
		
		// Read the size of the fingerprint
		fread(fingerprint_length_str,FP_LENGTH_SIZE,1,query_file);
		
		// Convert red 4 bytes into unsigned int
		fingerprint_length_int = (unsigned int)fingerprint_length_str[0] << 24 
			| (unsigned int)fingerprint_length_str[1] << 16 
			| (unsigned int)fingerprint_length_str[2] << 8 
			| (unsigned int)fingerprint_length_str[3]
			;
		
		fingerprint_byte_length_int = fingerprint_length_int / 8; // Because the size is given in bit number, so we convert it to byte number

		// Read the fingerprint
		fread(query_fp, fingerprint_byte_length_int, 1, query_file);
		A=0;
		for(k=0;k<fingerprint_byte_length_int;k++){
			A += popcount(query_fp[k]);
		}
		
		molecule_results_list = PyList_New(0);
		
		molecule_hit_count = 0;
		tc_sum = 0;
		squared_tc_sum = 0;
		
		PyBytes_AsStringAndSize(
			PyList_GetItem(
				database_file_name_list
				, fingerprint_number
			)
			, &db_bytes
			, &db_size
		);
		db_position = 0;
		// Loop over hits (database molecules)
		while( db_position < db_size) {	
			// Read database ID
			db_id_size = (size_t)db_bytes[db_position];
			db_position+=1;
			
			// Read the database molecule name
			reading_i = 0;
			while (reading_i < db_id_size) {
				id_chembl_mol[reading_i] = db_bytes[db_position];
				reading_i+=1;
				db_position+=1;
			}
			
			// Read the fingerprint
			reading_i = 0;
			while (reading_i < fingerprint_byte_length_int) {
				chembl_mol[reading_i] = db_bytes[db_position];
				reading_i+=1;
				db_position+=1;
			}

			TEMP_i += 1;
			B=0;
			c=0;
			// Compare molecules A and B
			for(k=0;k<fingerprint_byte_length_int;k++){
				B += popcount(chembl_mol[k]);
				c += popcount(query_fp[k]&chembl_mol[k]);
			}
			
			// Compute tanimoto
			tanimoto = ((double)c)/(A+B-c);
			molecule_hit_count = molecule_hit_count + 1;
			tc_sum += tanimoto;
			squared_tc_sum += pow(tanimoto, 2.0);
			
			// Lets pythonise these results
			db_molecule_id = PyUnicode_FromStringAndSize(id_chembl_mol, db_id_size);
			tanimoto_score = PyFloat_FromDouble(tanimoto);
			
			
			// current_array_0 = PyDict_GetItem(db_tanimoto_dict, db_molecule_id); // WARNING : code here note up to date : possible memory leaks
			// if (current_array_0) { // Append the tc score no matter what
				// PyList_Append(current_array_0, tanimoto_score);
			// }else{
				// current_array_0 = PyList_New(1);
				// PyList_SetItem(current_array_0,PyLong_AsSsize_t(PyLong_FromLong(0)), tanimoto_score);
				// PyDict_SetItem(db_tanimoto_dict, db_molecule_id, current_array_0);
			// }
			
			current_array_0 = PyDict_GetItem(db_tanimoto_dict, db_molecule_id); // return NULL if not found. NULL tested as false in boolean context
			if (fingerprint_number == 0) { // Append tc score for final results only if this is the first loop or if another tc score has been computed
				current_array_0 = PyList_New(1);
				PyList_SetItem(current_array_0, 0, tanimoto_score);
				Py_INCREF(tanimoto_score);
				PyDict_SetItem(db_tanimoto_dict, db_molecule_id, current_array_0);
				Py_DECREF(current_array_0);
			} else if (current_array_0) {
				PyList_Append(current_array_0, tanimoto_score);
			}
			
			result_row = PyList_New(inner_array_size);
			PyList_SetItem(result_row, db_id_index, db_molecule_id);
			PyList_SetItem(result_row, tc_index, tanimoto_score);
			PyList_Append(molecule_results_list, result_row); // Append all tc score to this object for normalization purpose. A row may be discarded from final result if missing tc value
			Py_DECREF(result_row);
		}
		
		if (normalize) {
			molecule_hit_count_double = (double)molecule_hit_count;
			tc_mean = tc_sum / molecule_hit_count_double;
			tc_stdev = sqrt(
				(squared_tc_sum / (molecule_hit_count_double - 1.0))
				- (pow(tc_sum, 2.0) / ( (molecule_hit_count_double - 1.0) * molecule_hit_count_double ))
			);

			// Now loop for normalization
			ii = 0;
			tc_mean_distance_sum = 0;
			while(ii < molecule_hit_count) {
				// Get current array
				current_array_0 = PyList_GetItem(
					molecule_results_list
					, ii // loop index
				);
				
				// Extract tc value from current array
				tc_stdev_loop = PyFloat_AsDouble(
					PyList_GetItem(
						current_array_0
						, tc_index // Postion of the tanimoto coefficient inside the inner list
					)
				);
				
				// Compute zscore
				zscore = (tc_stdev_loop - tc_mean) / tc_stdev;
				pyfloat_buffer = PyFloat_FromDouble(zscore);
				
				// Put zscore in the array's last spot
				PyList_SetItem(
					current_array_0
					, zscore_index
					, pyfloat_buffer // Transfer the ownership to this array ...
				);
				Py_INCREF(pyfloat_buffer); // Take ownership
				// Put normalized value in dict
				current_array_1 = PyDict_GetItem(
					db_zscore_dict
					, PyList_GetItem(
						current_array_0
						, db_id_index // Postion of the db id inside the inner list
					)
				);
				if (current_array_1) { // If the array is borrow from the dict, we have to take ownership
					PyList_Append(current_array_1, pyfloat_buffer);
				}else{
					current_array_1 = PyList_New(1);
					PyList_SetItem(current_array_1, 0, pyfloat_buffer);// Transfer the ownership to this array ...
					Py_INCREF(pyfloat_buffer); 
					PyDict_SetItem(
						db_zscore_dict
						, PyList_GetItem(
							current_array_0
							, db_id_index // Postion of the db id inside the inner list
						)
						, current_array_1
					);
					Py_DECREF(current_array_1);
				}
				
				if (PyList_Size(current_array_1))
				
				Py_DECREF(pyfloat_buffer);
				ii += 1;
			}
		}
		// if (PyErr_Occurred()) {printf("Error occured\n");PyErr_Print();} else {printf("No Error so far\n");} // A nice string for python debugging
		Py_DECREF(molecule_results_list);
		fingerprint_number += 1;
	}
	

	if (normalize) {
		// Calculation of the zscore mean
		pos = 0;
		key_2_remove_list = PyList_New(0);
		while (PyDict_Next(db_zscore_dict, &pos, &key, &value)){
			// if (PyErr_Occurred()) {printf("Error occured\n");PyErr_Print();} else {printf("No Error so far\n");} // A nice string for python debugging
			pylong_buffer_0 = PyLong_FromSsize_t(PyList_Size(value));
			current_array_size_int = PyLong_AsLong(pylong_buffer_0);
			Py_DECREF(pylong_buffer_0);
			if (fingerprint_number == current_array_size_int){// check if the zscore list is same length as the number of fingerprint
				i = 0;
				zscore_sum = 0;
				zscore_mean = 0;
				// compute zscore mean
				while (i < current_array_size_int){
					zscore_sum += PyFloat_AsDouble(
						PyList_GetItem(
							value
							, i
						)
					);
						
					i +=1;
				}
				zscore_mean = zscore_sum / (double)current_array_size_int;
				pyfloat_buffer = PyFloat_FromDouble(zscore_mean);
				PyList_Append(value, pyfloat_buffer);
				Py_DECREF(pyfloat_buffer);
			} else {// if the zscore list miss some values, discard it 
				PyList_Append(key_2_remove_list, key);
			}
		}
		
		//Removing entry with missing zscore value
		// ii = 0;
		// l = PyLong_AsLong( PyLong_FromSsize_t( PyList_Size(key_2_remove_list)));
		// while (ii<l) {
			// PyDict_DelItem(
				// db_zscore_dict
				// , PyList_GetItem(key_2_remove_list, ii)
			// );
			// ii += 1;
		// }
		delete_keys_from_dict(db_zscore_dict, key_2_remove_list);
		Py_DECREF(key_2_remove_list);
	}
	
	fclose(query_file);
	
	if (normalize){
		return_dict = db_zscore_dict;
		Py_INCREF(db_zscore_dict);
	} else {
		return_dict = db_tanimoto_dict;
		Py_INCREF(db_tanimoto_dict);
	}
	
	if (is_tc_threshold | is_zscore_threshold) {
		// Remove rows according to the threshold
		key_2_remove_list = PyList_New(0);
		if (is_tc_threshold){ // According to tc threshold
			pos = 0;
			
			// Loop over hits
			while (PyDict_Next(db_tanimoto_dict, &pos, &key, &value)){
				i = 0;
				remove_value = 0;
				l = PyList_Size(value);
				while (i<l) { // loop over different fp tanimotos
					double_loop = PyFloat_AsDouble( 
						PyList_GetItem(
							value
							, i
						)
					);
					// Compare tanimoto coefficient to the user provided threshold
					if (double_loop < PyFloat_AsDouble(PyList_GetItem(tc_threshold_list, py_index))) {
						remove_value = 1; // Set it to 1 so we can remove it
					}
					i += 1;
				}
				if (remove_value) {
					PyList_Append(key_2_remove_list, key);
				}
				
			}
		}
		if (is_zscore_threshold & normalize){ // According to zscore
			pos = 0;
			while (PyDict_Next(db_zscore_dict, &pos, &key, &value)){
				i = 0;
				
				// Now determine the last index of the list to apply threshold on the last. Assume that the last float is the mean
				l = PyList_Size(value) - 1;
				if (
						PyFloat_AsDouble(
							PyList_GetItem(value, l) // Py float value of zscore mean
						)
						<= zscore_threshold
				) {
					PyList_Append(key_2_remove_list, key);
				}
			}
		}
		// Now we collected all the data to discard, we cure the result dictionnary that will be returned t opython code
		delete_keys_from_dict(return_dict, key_2_remove_list);
		Py_DECREF(key_2_remove_list);
	}
	
	// Deallocate variables
	Py_DECREF(db_tanimoto_dict);
	Py_DECREF(db_zscore_dict);
	// Py_DECREF(database_file_name_list);
	// Py_DECREF(tc_threshold_list);
	
	
	return return_dict;
}
