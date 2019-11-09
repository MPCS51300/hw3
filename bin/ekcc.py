import argparse

import sys, os
sys.path.insert(0, './')

import lexer
import yacc

parser = argparse.ArgumentParser(prog=sys.argv[0], usage="./bin/ekcc[.py] [-h|-?] [-v] [-O] [-emit-ast|-emit-llvm] -o <output-file> <input-file>", add_help=False)
parser.add_argument("-h", action="help", help="show this help message and exit")
parser.add_argument("-v", action='store_true', help="print information for debugging")
parser.add_argument("-O", action='store_true', help="enable optimization")
parser.add_argument("-emit-ast", action='store_true', help="dump AST in a YAML format")
parser.add_argument("-emit-llvm", action='store_true', help="output LLVM IR")
parser.add_argument("-o", help="set output file path", default=sys.stdout)
args, unknown = parser.parse_known_args()

if len(unknown) != 1:
    raise ValueError("Usage: ./bin/ekcc.py <input_file>")
else:
    if args.emit_ast == True:
        with open(unknown[0], 'r') as input:  
            content = input.read()
            result = yacc.parse(content)
            output_file_path = args.o
            if isinstance(args.o, str):
                with open(output_file_path, 'w') as output:
                    output.write(result)
            else:
                args.o.write(result)