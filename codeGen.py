from llvmlite import ir

def convert_type(type):
    if type == "int":
        return ir.IntType(32)
    elif type == "float":
        return ir.FloatType()
    elif type == "void":
        return ir.VoidType()
    elif type == "bool":
        return ir.IntType(1)
    elif "ref" in type:
        if "int" in type:
            return ir.PointerType(ir.IntType(32))
        elif type == "float":
            return ir.PointerType(ir.FloatType())
        elif type == "bool":
            return ir.PointerType(ir.IntType(1))


def convert_extern(ast, module):
    args = []
    ret_type = convert_type(ast["ret_type"])
    if "tdecls" in ast:
        for type in ast["tdecls"]["types"]:
            args.append(convert_type(type))

    fnty = ir.FunctionType(ret_type, args)
    func = ir.Function(module, fnty, name=ast["globid"])

def convert_externs(ast, module):
    for extern in ast["externs"]:
        convert_extern(extern, module)

def convert(ast, module):
    if "externs" in ast:
        convert_externs(ast["externs"], module)

import yaml
file = open("test_files/test1.ast.yaml", "r") 
ast = yaml.load(file.read(), Loader=yaml.FullLoader)
module = ir.Module(name="prog")
convert(ast, module)
print(module)
