from pathlib import Path
import typing
import csv
import re

CHEMBL_HEADER = 'CHEMBL'

ENCODING = {'encoding': 'utf-8'}

def list_way():
    file = Path('uniprot_database__ChEMBL_raw.csv').open('r', **ENCODING)
    od = csv.DictReader(file, delimiter='\t')
    rows = [{k: v for k, v in f.items()} for f in od]
    file.close()

    i = 0
    rows_to_remove = []
    rows_to_add = []
    print(len(rows))
    l = len(rows)
    while i < l:
        row: dict = rows[i]

        m = re.finditer(r'(CHEMBL[0-9]+)', row[CHEMBL_HEADER])
        match_list = [s.group() for s in m]
        if len(match_list) > 1:
            rows_to_remove.append(i)
            for chembl_id in match_list:
                r_tmp = row.copy()
                r_tmp[CHEMBL_HEADER] = chembl_id
                rows_to_add.append(r_tmp)
            rows.pop(i)
            l -= 1
        else:
            i += 1
    rows.extend(rows_to_add)

    print(len(rows))

    keys_list: typing.List[typing.Iterable[str]] = [a.keys() for a in rows]
    value_len_list = [len(a) for a in keys_list]
    key_list = keys_list[value_len_list.index(max(*value_len_list))]
    key_list = [key for key in key_list]
    print(key_list)
    file = Path('uniprot_database__ChEMBL.csv').open('w', newline='', **ENCODING)
    dw = csv.DictWriter(file, key_list, delimiter='\t')
    dw.writeheader()
    for row in rows:
        dw.writerow(row)
    file.close()


if __name__ == "__main__":
    list_way()



