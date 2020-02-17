__version__ = "1.2"

# Local packages
from src import texts
from src.misc import system_verification, clean_up
from src.workflow import start

# Python 3.7 Built-in packages
import time

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
    print(f"Elapsed time for the all script : {end_time - begin_time}.")



