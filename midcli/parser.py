import ply.lex as lex
import ply.yacc as yacc
import re

tokens = (
    'STRING', 'NAME', 'NAME_EQ', 'HEX', 'OCT', 'INTEGER',
	'FALSE', 'TRUE', 'NONE', 'LIST',
)


class Name(object):

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'<Name[{self.value}]>'

    def __str__(self):
        return self.value

    def __eq__(self, other):
        if not isinstance(other, str):
            return False
        return self.value == other


class Argument(object):

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return f'<Argument[{self.key}={self.value!r}]>'


def t_FALSE(t):
    r'false'
    t.value = False
    return t


def t_TRUE(t):
    r'true'
    t.value = True
    return t


def t_NONE(t):
    r'none'
    t.value = None
    return t


def t_HEX(t):
    r'0x[0-9a-fA-F]+'
    t.value = int(t.value, 16)
    return t


def t_OCT(t):
    r'0o[0-7]+'
    t.value = int(t.value, 8)
    return t


def t_INTEGER(t):
    r'\d+'
    t.value = int(t.value)
    return t


def t_LIST(t):
    r'([a-zA-Z0-9_\.\-+@#%]+,)+[a-zA-Z0-9_\.\-+=@#%]+'
    t.value = t.value.split(',')
    return t


def t_STRING(t):
    r'\"([^\\\n]|(\\.))*?\"'
    t.value = t.value[1:-1].encode().decode("unicode_escape")
    return t


def t_error(t):
    print("Illegal character %r" % t.value[0])
    t.lexer.skip(1)


t_ignore = ' \t'
t_NAME = r'[a-zA-Z][a-zA-Z0-9_-]+'
t_NAME_EQ = r'[a-zA-Z][a-zA-Z0-9_-]+='

start = 'input'


def p_input(p):
    'input : names'
    p[0] = p[1]

def p_input_args(p):
    'input : names arguments'
    p[0] = p[1] + p[2]


def p_names(p):
    '''
    names : NAME
    names : names NAME
    '''
    if len(p) == 2:
        p[0] = [Name(p[1])]
    else:
        p[1].append(Name(p[2]))
        p[0] = p[1]


def p_arguments(p):
    '''
    arguments : argument
    arguments : arguments argument
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[1].append(p[2])
        p[0] = p[1]


def p_argument(p):
    'argument : NAME_EQ literal'
    p[0] = Argument(p[1][:-1], p[2])


def p_literal(p):
    '''
    literal : HEX
    literal : OCT
    literal : INTEGER
    literal : TRUE
    literal : FALSE
    literal : NONE
    literal : LIST
    literal : NAME
    literal : STRING
    '''
    p[0] = p[1]


def p_error(p):
    if p:
        print(f'syntax error at {p.value!r} {p.type}')
    else:
        print('syntax error')


lexer = lex.lex(reflags=re.UNICODE)
parser = yacc.yacc(debug=True, optimize=True)


def parse(s):
    lexer.parens = 0
    lexer.seen_quote = False
    lexer.seen_lparen = False
    parser.input = s
    parser.filename = '<stdin>'
    return parser.parse(s, lexer=lexer, tracking=True)
