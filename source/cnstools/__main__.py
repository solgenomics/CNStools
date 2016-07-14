"""The main script for the cnstools program, its only job is to import the cnstools python package and then run the specified task module with the remaining arguements"""
import sys
import __init__ as cnstools
program_run_dict = {}

#import and create dictionary of the functions to run each __all__ named task module with file arguements
for module in cnstools.__all__:
    exec "program_run_dict['%s'] = cnstools.%s.file_run"%(module,module)

def main():
    """runs the task module given in the first cmdline arguemnt with the cmdline arguements that follow as arguements"""
    cnstools.identify.header_print(sys.argv[1])
    program_run_dict[sys.argv[1].strip()](*(sys.argv[2:]))
  
if __name__ == '__main__':
    main()