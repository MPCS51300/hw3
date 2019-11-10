import argparse, sys
import lexer, yacc
import yaml

parser = argparse.ArgumentParser(prog=sys.argv[0], 
                                 description='Compiler',
                                 usage="python3 ekcc.py [-h|-?] [-v] [-O] [-emit-ast|-emit-llvm] -o <output-file> <input-file>", 
                                 add_help=False)
parser.add_argument("-h", action="help", help="show this help message and exit")
parser.add_argument("-v", action="store_true", help="print information for debugging")
parser.add_argument("-O", action="store_true", help="enable optimization")
parser.add_argument("-emit-ast", action="store_true", default=False, help="generate AST")
parser.add_argument("-emit-llvm", action="store_true", default=False, help="generate LLVM IR")
parser.add_argument("-o", action="store", default=sys.stdout, help="set output file path")
args, unknown = parser.parse_known_args()

if len(unknown) != 1:
    raise ValueError("Usage: python3 ekcc.py <input_file>")
else:
    if args.emit_ast == True:
        with open(unknown[0], 'r') as input:  
            content = input.read()
            ast = yacc.parse(content)
            ast_in_yaml = yaml.dump(ast)
            output_file_path = args.o
            if isinstance(args.o, str):
                with open(output_file_path, 'w') as output:
                    output.write(ast_in_yaml)
            else:
                args.o.write(ast_in_yaml)