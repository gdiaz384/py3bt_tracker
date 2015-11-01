import argparse

command_Line_parser = argparse.ArgumentParser()
command_Line_parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
command_Line_parser.add_argument("-o", "--enable_obfuscation", help="seed database with random IP addresses", action="store_true")

command_Line_arguments = command_Line_parser.parse_args()

if command_Line_arguments.verbose:
    print("verbosity turned on")
    
if command_Line_arguments.enable_obfuscation:
    print("obfuscation turned on")