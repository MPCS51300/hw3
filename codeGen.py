from llvmlite import ir

def generate_type(type):
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


def generate_extern(ast, module):
    args = []
    ret_type = generate_type(ast["ret_type"])
    if "tdecls" in ast:
        for type in ast["tdecls"]["types"]:
            args.append(generate_type(type))

    fnty = ir.FunctionType(ret_type, args)
    func = ir.Function(module, fnty, name=ast["globid"])

def generate_externs(ast, module):
    for extern in ast["externs"]:
        generate_extern(extern, module)

def generate_binop(ast, module, builder):
    op = ast["op"]
    # if op == "lt":

def generate_exp(ast, module, builder):
    name = ast["name"]
    if name == "binop":
        generate_binop(ast, module, builder)

def generate_stmt(ast, module, builder):
    name = ast["name"]
    print(ast.keys())
    if name == "if":
        pred = generate_exp(ast["cond"], module, builder)
        print("if")

        # if "else_stmt" in ast:
        #     with builder.if_else(pred) as (then, otherwise):
        #         with then:
        #         with otherwise:

        #     print("if .. else")
        # else:

        
    # elif name == "ret":
    # elif name == "vardeclstmt":
    # elif name == "expstmt":
    # elif name == "while":
    # elif name == "print":
    # elif name == "printslit":

def generate_blk(ast, module, builder):
    if "contents" in ast:
        for stmt in ast["contents"]["stmts"]:
            generate_stmt(stmt, module, builder)

def generate_func(ast, module):
    args = []
    ret_type = generate_type(ast["ret_type"])
    if "vdecls" in ast:
        for vdecl in ast["vdecls"]["vars"]:
            args.append(generate_type(vdecl["type"]))

    fnty = ir.FunctionType(ret_type, args)
    func = ir.Function(module, fnty, name=ast["globid"])

    # Now implement the function
    entry_block = func.append_basic_block(name="entry")
    builder = ir.IRBuilder(entry_block)

    if "blk" in ast:
        result = generate_blk(ast["blk"], module, builder)
    
    builder.ret(result)

def generate_funcs(ast, module):
    for func in ast["funcs"]:
        generate_func(func, module)

def convert(ast, module):
    if "externs" in ast:
        generate_externs(ast["externs"], module)

    if "funcs" in ast:
        generate_funcs(ast["funcs"], module)

import yaml
file = open("test_files/test1.ast.yaml", "r") 
ast = yaml.load(file.read(), Loader=yaml.FullLoader)
module = ir.Module(name="prog")
convert(ast, module)
print(module)

