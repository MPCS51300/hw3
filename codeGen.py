from llvmlite import ir
import yaml

variables = {} # track variables: key=current_function_variable_name, value:llvmlite_type
current_func_prefix = None # track the current funtion

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
    exptype = ast["exptype"]
    lhs = generate_exp(ast["lhs"], module, builder)
    rhs = generate_exp(ast["rhs"], module, builder)

    #todo: what if lhs, rhs is ref 

    if exptype == "bool":
        if op == "and":
            return builder.and_(lhs, rhs)
        elif op == "or":
            return builder.or_(lhs, rhs)
        else:
            if ast["lhs"]["exptype"] == "int": 
                if op == "lt":
                    return builder.icmp_signed("<", lhs, rhs)
                elif op == "gt":
                    return builder.icmp_signed(">", lhs, rhs)
                elif op == "eq":
                    return builder.icmp_signed("==", lhs, rhs)
            elif ast["lhs"]["exptype"] == "float":
                if op == "lt":
                    return builder.fcmp_ordered("<", lhs, rhs)
                elif op == "gt":
                    return builder.fcmp_ordered(">", lhs, rhs)
                elif op == "eq":
                    return builder.fcmp_ordered("==", lhs, rhs)
    elif exptype == "int":
        if op == "add":
            return builder.add(lhs, rhs)
        elif op == "sub":
            return builder.sub(lhs, rhs)
        elif op == "mul":
            return builder.mul(lhs, rhs)
        elif op == "div":
            return builder.udiv(lhs, rhs)
    elif exptype == "float":
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

def generate_uop(ast, module, builder):
    op = ast["op"]
    exptype = ast["exptype"]
    if op == "not":
        return builder.not_(generate_exp(ast["exp"], module, builder))
    elif op == "minus":
        return builder.neg(generate_exp(ast["exp"], module, builder))
        
def generate_caststmt(ast, module, builder):
    typ = generate_type(ast["type"])
    return builder.bitcast(generate_exp(ast["exp"]), type)

def generate_assign(ast, module, builder):
    exp = generate_exp(ast["exp"], module, builder)
    dest = variables[ast["var"]] # find the value of ast["var"] in variables
    builder.store(exp, dest.as_pointer())

def generate_funccall(ast, module, builder):
    fn = module.get_global(ast["globid"])
    args = []
    if "params" not in ast or "exps" not in ast["params"]:
        pass
    else:
        for exp in ast["params"]["exps"]:
            print("exp:", exp)
            args.append(generate_exp(exp, module, builder))
    return builder.call(fn, args)

def generate_exp(ast, module, builder):
    name = ast["name"]
    if name == "binop":
        return generate_binop(ast, module, builder)
    elif name == "caststmt":
        return generate_caststmt(ast, module, builder)
    elif name == "uop":
        return generate_uop(ast, module, builder)
    elif name == "lit":
        return ir.Constant(generate_type(ast["exptype"]), ast["value"])
    elif name == "varval":
        current_variable = current_func_prefix + " " + ast["var"]
        variables[current_variable] = ir.Constant(generate_type("int"), 0)
        return variables[current_variable] # it should return the actual llvmlite type 
    elif name == "assign":
        return generate_assign(ast, module, builder)
    elif name == "funccall":
        return generate_funccall(ast, module, builder)

def generate_stmt(ast, module, builder):
    name = ast["name"]
    if name == "if":
        pred = generate_exp(ast["cond"], module, builder)
        res = builder.if_then(pred)
        with builder.if_then(pred) as (then):
            # with then:
            #     print(then)
            #     
            generate_stmt(ast["stmt"], module, builder)

        
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
    global current_func_prefix
    if current_func_prefix == None:
        current_func_prefix = ast["globid"]

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

    current_func_prefix = None

def generate_funcs(ast, module):
    for func in ast["funcs"]:
        generate_func(func, module)

def convert(ast, module):
    if "externs" in ast:
        generate_externs(ast["externs"], module)

    if "funcs" in ast:
        generate_funcs(ast["funcs"], module)


file = open("test_files/test1_ekcc.yml", "r") 
ast = yaml.load(file.read(), Loader=yaml.FullLoader)
module = ir.Module(name="prog")
convert(ast, module)
print(module)

