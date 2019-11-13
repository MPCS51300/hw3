from llvmlite import ir
import yaml

variables = {} # track variables: key=current_function_variable_name, value:llvmlite_type
current_func_prefix = None # track the current funtion

#read print and printslit functions' IR
with open("print.ll", "r") as input:  
    llvm_ir = input.read()

def create_execution_engine():
    """
    Create an ExecutionEngine suitable for JIT code generation on
    the host CPU.  The engine is reusable for an arbitrary number of
    modules.
    """
    # Create a target machine representing the host
    target = llvm.Target.from_default_triple()
    target_machine = target.create_target_machine()
    # And an execution engine with an empty backing module
    backing_mod = llvm.parse_assembly("")
    engine = llvm.create_mcjit_compiler(backing_mod, target_machine)
    return engine


def compile_ir(engine, llvm_ir):
    """
    Compile the LLVM IR string with the given engine.
    The compiled module object is returned.
    """
    # Create a LLVM module object from the IR
    mod = llvm.parse_assembly(llvm_ir)
    mod.verify()
    engine.add_module(mod)
    engine.finalize_object()
    engine.run_static_constructors()
    return mod

#generate print function codes
engine = create_execution_engine()
print_module = compile_ir(engine, llvm_ir)

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

def generate_stmt(ast, module, builder, func):
    name = ast["name"]
    if name == "blk":
        generate_blk(ast, module, builder)
    elif name == "if":
        pred = generate_exp(ast["cond"], module, builder)
        if "else_stmt" in ast:
            with builder.if_else(pred) as (then, otherwise):
                with then:
                    generate_stmt(ast["stmt"], module, builder)
                with otherwise:
                    generate_stmt(ast["else_stmt"], module, builder)
        else:
            with builder.if_then(pred) as (then):
                with then:
                    generate_stmt(ast["stmt"], module, builder)
    elif name == "ret":
        if "exp" in ast:
            generate_exp(ast["exp"], module, builder)
    elif name == "vardeclstmt":  
        var = builder.alloca(generate_type(ast["vdecl"]["type"], name = ast["vdecl"]["var"]))
        builder.store(generate_exp(ast["exp"], module, builder), var)
    elif name == "expstmt":
        generate_exp(ast["exp"], module, builder)
    elif name == "while":
        loop_head = func.append_basic_block("loop.header")
        loop_body = func.append_basic_block("loop.body")
        loop_end = func.append_basic_block("loop.end")
        builder.branch(loop_head)
        builder.position_at_end(loop_head)
        cond = generate_exp(ast["cond"], module, builder)
        builder.cbranch(cond, loop_body, loop_end)
        builder.position_at_end(loopbody)
        #loop body
        generate_stmt(ast["stmt"], module, builder, func)
        #jump to loop head
        builder.branch(loop_head)
        builder.position_at_end(loop_end)
    elif name == "print":
        args = []
        args.append(generate_exp(ast["exp"], module, builder))
        fn = print_module.get_global("print")
        builder.call(fn, args)
    elif name == "printslit":
        args = []
        args.append(generate_slit(ast["string"]))
        fn = print_module.get_global("printslit")
        builder.call(fn, args)

def generate_blk(ast, module, builder, func):
    if "contents" in ast:
        for stmt in ast["contents"]["stmts"]:
            generate_stmt(stmt, module, builder, func)

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
        result = generate_blk(ast["blk"], module, builder, func)
    
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

