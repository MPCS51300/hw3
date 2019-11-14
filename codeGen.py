from llvmlite import ir
import llvmlite.binding as llvm
import yaml


#read print and printslit functions' IR
with open("print.ll", "r") as input:  
    llvm_ir = input.read()

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
    elif type == "slit":
        return ir.PointerType(ir.IntType(8))

def generate_slit(string):
    return ir.Constant(generate_type("slit"), string)

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

def generate_binop(ast, module, builder, variables):
    op = ast["op"]
    exptype = ast["exptype"]

    lhs = generate_exp(ast["lhs"], module, builder, variables)
    rhs = generate_exp(ast["rhs"], module, builder, variables)
    # load if it is a pointer
    if lhs.type.is_pointer:
        lhs = builder.load(lhs)
    if rhs.type.is_pointer:
        rhs = builder.load(rhs)

    if exptype == "bool":
        if op == "and":
            return builder.and_(lhs, rhs)
        elif op == "or":
            return builder.or_(lhs, rhs)
        else:
            if "int" in ast["lhs"]["exptype"]: 
                if op == "lt":
                    return builder.icmp_signed("<", lhs, rhs)
                elif op == "gt":
                    return builder.icmp_signed(">", lhs, rhs)
                elif op == "eq":
                    return builder.icmp_signed("==", lhs, rhs)
            elif "float" in ast["lhs"]["exptype"]:
                if op == "lt":
                    return builder.fcmp_ordered("<", lhs, rhs)
                elif op == "gt":
                    return builder.fcmp_ordered(">", lhs, rhs)
                elif op == "eq":
                    return builder.fcmp_ordered("==", lhs, rhs)
    elif "int" in exptype:
        if op == "add":
            return builder.add(lhs, rhs)
        elif op == "sub":
            return builder.sub(lhs, rhs)
        elif op == "mul":
            return builder.mul(lhs, rhs)
        elif op == "div":
            return builder.udiv(lhs, rhs)
    elif "float" in exptype:
        if op == "add":
            return builder.fadd(lhs, rhs)
        elif op == "sub":
            return builder.fsub(lhs, rhs)
        elif op == "mul":
            return builder.fmul(lhs, rhs)
        elif op == "div":
            return builder.fdiv(lhs, rhs)
    elif exptype == "void":
        pass

def generate_uop(ast, module, builder, variables):
    op = ast["op"]
    exptype = ast["exptype"]
    if op == "not":
        return builder.not_(generate_exp(ast["exp"], module, builder, variables))
    elif op == "minus":
        return builder.neg(generate_exp(ast["exp"], module, builder, variables))
        
def generate_caststmt(ast, module, builder):
    typ = generate_type(ast["type"])
    return builder.bitcast(generate_exp(ast["exp"]), type)

def generate_assign(ast, module, builder, variables):
    exp = generate_exp(ast["exp"], module, builder, variables)
    builder.store(exp, variables[ast["var"]])

def generate_funccall(ast, module, builder, variables):
    fn = module.get_global(ast["globid"])
    args = []
    if "params" not in ast or "exps" not in ast["params"]:
        pass
    else:
        for exp in ast["params"]["exps"]:
            args.append(generate_exp(exp, module, builder, variables))
    return builder.call(fn, args)

def generate_exp(ast, module, builder, variables):
    name = ast["name"]
    if name == "binop":
        return generate_binop(ast, module, builder, variables)
    elif name == "caststmt":
        return generate_caststmt(ast, module, builder)
    elif name == "uop":
        return generate_uop(ast, module, builder, variables)
    elif name == "lit":
        return ir.Constant(generate_type(ast["exptype"]), ast["value"])
    elif name == "varval":
        return variables[ast["var"]] 
    elif name == "assign":
        return generate_assign(ast, module, builder, variables)
    elif name == "funccall":
        return generate_funccall(ast, module, builder, variables)

def generate_stmt(ast, module, builder, func, variables):
    name = ast["name"]
    if name == "blk":
        generate_blk(ast, module, builder, func, variables)
    elif name == "if":
        pred = generate_exp(ast["cond"], module, builder, variables)
        if "else_stmt" in ast:
            with builder.if_else(pred) as (then, otherwise):
                with then:
                    generate_stmt(ast["stmt"], module, builder, func, variables)
                with otherwise:
                    generate_stmt(ast["else_stmt"], module, builder, func, variables)
        else:
            with builder.if_then(pred):
                generate_stmt(ast["stmt"], module, builder, func, variables)
    elif name == "ret":
        if "exp" in ast:
            exp = generate_exp(ast["exp"], module, builder, variables)
            if exp.type.is_pointer:
                builder.load(exp)
            builder.ret(exp)
        else:
            builder.ret_void()
    elif name == "vardeclstmt": 
        variables[ast["vdecl"]["var"]] = builder.alloca(generate_type(ast["vdecl"]["type"]))
        builder.store(generate_exp(ast["exp"], module, builder, variables), variables[ast["vdecl"]["var"]])
    elif name == "expstmt":
        generate_exp(ast["exp"], module, builder, variables)
    elif name == "while":
        loop_head = func.append_basic_block("loop.header")
        loop_body = func.append_basic_block("loop.body")
        loop_end = func.append_basic_block("loop.end")
        builder.branch(loop_head)
        builder.position_at_end(loop_head)
        cond = generate_exp(ast["cond"], module, builder, variables)
        builder.cbranch(cond, loop_body, loop_end)
        builder.position_at_end(loop_body)
        #loop body
        generate_stmt(ast["stmt"], module, builder, func, variables)
        #jump to loop head
        builder.branch(loop_head)
        builder.position_at_end(loop_end)
    # elif name == "print":
    #     args = []
    #     args.append(generate_exp(ast["exp"], module, builder))
    #     fn = print_module.get_global("print")
    #     builder.call(fn, args)
    # elif name == "printslit":
    #     args = []
    #     args.append(generate_slit(ast["string"]))
    #     fn = print_module.get_global("printslit")
    #     builder.call(fn, args)

def generate_blk(ast, module, builder, func, variables):
    if "contents" in ast:
        for stmt in ast["contents"]["stmts"]:
            generate_stmt(stmt, module, builder, func, variables)

def generate_func(ast, module):
    args_types = [] # the types of args in llvmlite
    args_names = [] # the names of args in llvmlite
    variables = {}  # the local vairables in the current function, key: variable name, value: variable type
    ret_type = generate_type(ast["ret_type"])
    if "vdecls" in ast:
        for vdecl in ast["vdecls"]["vars"]:
            args_types.append(generate_type(vdecl["type"]))
            args_names.append(vdecl["var"])

    # Adds function to module
    fnty = ir.FunctionType(ret_type, args_types)
    func = ir.Function(module, fnty, name=ast["globid"])

    # Adds entry block to the function
    entry_block = func.append_basic_block(name="entry")
    builder = ir.IRBuilder(entry_block)

    # Allocates function arguments
    for arg, name in zip(func.args, args_names):
        if arg.type.is_pointer:
            variables[name] = arg
        else:
            ptr = builder.alloca(arg.type)
            variables[name]= ptr
            builder.store(arg, ptr)
    
    if "blk" in ast:
        result = generate_blk(ast["blk"], module, builder, func, variables)

    # Returns void if return type is void
    if ast["ret_type"] == "void":
        builder.ret_void()
    
def generate_funcs(ast, module):
    for func in ast["funcs"]:
        generate_func(func, module)

def generate_prog(ast, module):
    if "externs" in ast:
        generate_externs(ast["externs"], module)

    generate_funcs(ast["funcs"], module)

# The function called by ekcc.py
def generate_code(ast):
    module = ir.Module(name="prog")
    generate_prog(ast, module)
    return module

