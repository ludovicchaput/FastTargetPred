__version__ = "1.2"

# Python 3.7 Built-in packages
import time
import sys

try:
    assert float(sys.version_info[0].__str__() + "." + sys.version_info[1].__str__()) >= 3.7
except AssertionError:
    print("This program only works with Python 3.7+ version. Please install a newer python version.")
    sys.exit(1)

# Local packages
from src import texts
from src.misc import system_verification, clean_up
from src.workflow import start

def main():
    print(texts.app_header.format(__version__))
    print(texts.check_system, end='')
    system_ok, messages = system_verification()
    if system_ok:
        print(texts.checked)
        start()
    else:
        print(texts.system_not_ok + '\n\t'.join(messages))
    clean_up()



if __name__ == "__main__":
    begin_time = time.time()
    main()
    end_time = time.time()
    print("Elapsed time for the all script : {}.".format(end_time - begin_time))



