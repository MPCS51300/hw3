import ply.yacc as yacc
import lexer

tokens = lexer.tokens 


#######
# Parser
#######

precedence = (
    ('right', 'ASSIGN'),
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'EQUAL'),
    ('left', 'SMALLERTHAN', 'GREATERTHAN'), 
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('right', 'NEGATE'),
 )

def p_prog(p):
    '''
    prog : externs funcs
    '''
    p[0] = {"name" : "prog"}
    p[0]["externs"] = p[1]
    p[0]["funcs"] = p[2]

def p_externs(p):
    '''
    externs : 
            | extern
            | extern externs
    '''
    p[0] = {"name" : "externs"}
    if len(p) >= 2:
        p[0]["externs"] = [p[1]]
    if len(p) == 3:
        if "externs" in p[2]:
            p[0]["externs"].extend(p[2]["externs"])

def p_funcs(p):
    '''
    funcs : func
          | func funcs
    '''
    p[0] = {"name" : "funcs"}
    p[0]["funcs"] =[p[1]]
    if len(p) == 3:
        if "funcs" in p[2]:
            p[0]["funcs"].extend(p[2]["funcs"])

def p_extern(p):
    '''
    extern : EXTERN type globid LPARENTHESE RPARENTHESE SEMICOLON
           | EXTERN type globid LPARENTHESE tdecls RPARENTHESE SEMICOLON
    '''
    p[0] = {"name" : "extern"}
    p[0]["ret_type"] = p[2]
    p[0]["globid"]  = p[3]
    if len(p) == 8:
        p[0]["tdecls"] = p[5]

def p_func(p):
    '''
    func : DEF type globid LPARENTHESE RPARENTHESE blk
         | DEF type globid LPARENTHESE vdecls RPARENTHESE blk
    '''
    p[0] = {"name" : "func"}
    p[0]["ret_type"] = p[2]
    p[0]["globid"]  = p[3]
    if len(p) == 7:
        p[0]["blk"] = p[6]
    if len(p) == 8:
        p[0]["vdecls"] = p[5]
        p[0]["blk"] = p[7]


    

def p_blk(p):
    '''
    blk : LBRACE RBRACE
        | LBRACE stmts RBRACE
    '''
    p[0] = {"name" : "blk"}
    if len(p) == 4:
        p[0]["contents"] = p[2]


def p_stmts(p):
    '''
    stmts : stmt
          | stmt stmts
    '''
    p[0] = {"name" : "stmts"}
    p[0]["stmts"] = [p[1]]
    if len(p) == 3:
        if "stmts" in p[2]:
            p[0]["stmts"].extend(p[2]["stmts"])

def p_stmt0(p):
    '''
    stmt : blk
         | RETURN SEMICOLON
         | RETURN exp SEMICOLON
         | vdecl ASSIGN exp SEMICOLON
         | exp SEMICOLON
         | WHILE LPARENTHESE exp RPARENTHESE stmt
         | IF LPARENTHESE exp RPARENTHESE stmt
         | IF LPARENTHESE exp RPARENTHESE stmt ELSE stmt
         | PRINT exp SEMICOLON
    '''
    p[0] = {}
    if len(p) == 2:
        p[0] = p[1]
    elif p[1] == "return":
        p[0]["name"] = "ret"
        if len(p) == 4:
            p[0]["exp"] = p[2]
    elif len(p) == 5:
        p[0]["name"] = "vardeclstmt"
        p[0]["vdecl"] = p[1]
        p[0]["exp"] = p[3]
    elif len(p) == 3:
        p[0]["name"] = "expstmt"
        p[0]["exp"] = p[1]
    elif p[1] == "while":
        p[0]["name"] = "while"
        p[0]["cond"] = p[3]
        p[0]["stmt"] = p[5]
    elif p[1] == "if":
        p[0]["name"] = "if"
        p[0]["cond"] = p[3]
        p[0]["stmt"] = p[5]
        if len(p) == 8:
            p[0]["else_stmt"] = p[7]
    elif p[1] == "print":
            p[0]["name"] = "print"
            p[0]["exp"] = p[2]

def p_stmt1(p):
    '''
    stmt : PRINT SLIT SEMICOLON
    '''
    p[0] = {"name" : "printslit", "string" : p[2]}

def p_exps(p):
    '''
    exps : exp
         | exp COMMA exps
    ''' 
    p[0] = {"name" : "exps"}
    if len(p) >= 2:
        p[0]["exps"] = [p[1]]    
    if len(p) == 4:
        if "exps" in p[3]:
            p[0]["exps"].extend(p[3]["exps"])

def p_exp0(p):
    '''
    exp : LPARENTHESE exp RPARENTHESE
        | binop
        | uop
        | globid LPARENTHESE exps RPARENTHESE
        | globid LPARENTHESE RPARENTHESE
    '''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 4:
        p[0] = p[2]
    elif p[1]=="(":
        p[0] = {
            "name": "funccall",
            "globid": p[1],
            "params": p[3]
        }
    else:
        p[0] = {
            "name": "funccall",
            "globid": p[1],
            "params": p[3]
        }

def p_exp1(p):
    '''
    exp : VARID
    '''
    p[0] = {
        "name": "varval",
        "var": p[1]
    }

def p_exp2(p):
    '''
    exp : lit
    '''
    p[0] = p[1]

def p_binop(p):
    '''
    binop : arith-ops
          | logic-ops
          | VARID ASSIGN exp
          | LBRACKET type RBRACKET exp
    '''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 4:
        p[0] = {
            "name": "assign",
            "var": p[1],
            "exp": p[3]
        }
    else:
        p[0] = {
            "name": "caststmt",
            "type": p[2],
            "exp": p[4]
        }

def p_arithOps(p):
    '''
    arith-ops : exp TIMES exp
              | exp DIVIDE exp
              | exp PLUS exp
              | exp MINUS exp
    '''
    op = ""
    if p[2] == '+':
        op = "add"
    elif p[2] == '-':
        op = "sub"
    elif p[2] == '*':
        op = "mul"
    elif p[2] == '/':
        op = "div"
    p[0] = {
        "name": "binop",
        "op": op,
        "lhs": p[1],
        "rhs": p[3]
    }

def p_logicOps(p):
    '''
    logic-ops : exp EQUAL exp
              | exp SMALLERTHAN exp
              | exp GREATERTHAN exp
              | exp AND exp
              | exp OR exp
    '''
    op = ""
    if p[2] == "==":
        op = "eq"
    elif p[2] == "<":
        op = "lt"
    elif p[2] == ">":
        op = "gt"
    elif p[2] == "&&":
        op = "and"
    elif p[2] == "||":
        op = "or"
    p[0] = {
        "name": "binop",
        "op": op,
        "lhs": p[1],
        "rhs": p[3]
    }


def p_uop(p):
    '''
    uop : NEGATE exp 
        | MINUS exp
    '''
    if p[1]=='!':
        p[0] = {
            "name": "uop",
            "op": "not",
            "exp": p[2]
        }
    else:
        p[0] = {
            "name": "uop",
            "op": "minus",
            "exp": p[2]
        }

def p_lit0(p):
    '''
    lit : true
        | false
    '''
    p[0] = p[1]

def p_lit1(p):
    '''
    lit : FNUMBER
    '''
    p[0] = {
        "name": "flit",
        "value": p[1]
    }

def p_lit2(p):
    '''
    lit : NUMBER
    '''
    p[0] = {
        "name": "lit",
        "value": p[1]
    }

def p_true(p):
    '''
    true : TRUE
    '''

def p_false(p):
    '''
    false : FALSE
    '''

def p_globid(p):
    '''
    globid : IDENT
    '''
    p[0] = p[1]

def p_type(p):
    '''
    type : INT
         | CINT
         | FLOAT
         | BOOL
         | VOID
    '''
    p[0] = p[1]

def p_refType(p):
    '''
    type : REF type
    '''
    p[0] = 'ref ' + p[2]

def p_noAliasRefType(p):
    '''
    type : NOALIAS REF type
    '''
    p[0] = 'noalias ref ' + p[3]

def p_vdecls(p):
    '''
    vdecls : vdecl COMMA vdecls
           | vdecl
    '''
    p[0] = {"name" : "vdecls"}
    if len(p) >= 2:
        p[0]["vars"] = [p[1]]    
    if len(p) == 4:
        if "vars" in p[3]:
            p[0]["vars"].extend(p[3]["vars"])

def p_tdecls(p):
    '''
    tdecls : type
           | type COMMA tdecls
    '''
    p[0] = {"name" : "tdecls"}
    if len(p) >= 2:
        p[0]["types"] = [p[1]]    
    if len(p) == 4:
        if "types" in p[3]:
            p[0]["types"].extend(p[3]["types"])

def p_vdecl(p):
    '''
    vdecl : type VARID
    '''
    p[0] = {
        "node": "vdecl",
        "type": p[1],
        "var": p[2]
    }

def parse(input_content):
    parser = yacc.yacc()
    return parser.parse(input_content)