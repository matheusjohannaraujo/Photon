# Photon parser
# This script converts lines of photon code into tokens
# and also generates the struct of the code.
# This struct is used by the Engine to execute the code.

import re
from lexer import *

statements = ['if','else','elif','def','cdef','for','in','as','return','import','class','while','break','continue','try', 'del']
operators = ['+','-','%','/','*','**','<','>','not', '!', 'and','or','is', '&']
builtins = ['input','sizeof','addr']
types = ['str','cstr','const','struct','char','int','float','double','struct', 'func','uint','ulong','ubyte','file']
symbols = {
    '.':'dot',
    '=':'equal',
    ':':'beginBlock',
    '(':'lparen',
    ')':'rparen',
    ',':'comma',
    '[':'lbracket',
    ']':'rbracket',
    "'":'singleQuote',
    '"':'doubleQuote',
    '#':'hashtag',
    ' ':'space',
    '\n':'newLine',
    '\t':'tab',
    '{':'lbrace',
    '}':'rbrace',
    '>':'greaterThan',
    '<':'lessThan',
    '_':'underline'
}

lineNumber = 0
currentFilename = ''
currentLine = ''
parsePhrase = ''

DEBUG = False

def debug(*args, center=False):
    if DEBUG:
        if center:
            consoleWidth = os.get_terminal_size()[0]
            print(args[0].center(consoleWidth, '-'))
        else:    
            print(*args)

def parse(line, filename='', no=-1, debug=False):
    global currentLine, lineNumber, currentFilename, DEBUG
    ''' Return a list of tokens for the given line '''
    DEBUG = debug
    lineNumber = no
    currentFilename = filename
    currentLine = line
    tokens = [i for i in re.split('(\W)',line) if not i == '' ]
    indentation = 0
    indentationSet = False
    tokenized = []
    preserveSpace = False
    quote = ''
    for n, i in enumerate(tokens):
        if not indentationSet and not (i == ' ' or i == '\t'):
            indentationSet = True
            tokenized.append({'token':'indent','indent':indentation})
        if (i == ' ' or i == '\t') and not indentationSet:
            indentation += 1
        elif i in statements:
            tokenized.append({'token':i+'Statement'})
        elif i in operators:
            tokenized.append({'token':'operator','operator':i})
        elif i in types:
            tokenized.append({'token':'type','type':i})
        elif i in symbols:
            if i == ' ' and tokens[n+1] == '.' and tokenized[-1]['token'] in {'var', 'type'}:
                tokenized.append({'token':symbols[i], 'symbol':i})
                continue
            if i == "'" or i == '"':
                if not preserveSpace:
                    preserveSpace = True
                    quote = i
                elif preserveSpace and i == quote:
                    tokenized.append({'token':symbols[i],'symbol':i})
                    preserveSpace = False
                    quote = ''
            if not i in {'"', "'", ' ','\t','\n'} or (i in {'"',"'",' ','\t','\n'} and preserveSpace):
                tokenized.append({'token':symbols[i],'symbol':i})
        elif i in builtins:
            tokenized.append({'token':i})
        else:
            tokenized.append(inference(i))

    if tokenized == []:
        tokenized = [{'token':'indent','indent':0}]
    return tokenized

def token2word(tokens):
    phrase = ''
    for t in tokens:
        if t['token'] == 'indent':
            continue
        elif 'symbol' in t:
            phrase += t['symbol']
        elif t['token'] in {'num', 'var', 'expr','print','printFunc',
                'floatNumber', 'type',
                'assign','operator','group','ifStatement','if','elifStatement',
                'elif','input','inputFunc', 'args','call', 'whileStatement',
                'while','forStatement','inStatement','for','range','defStatement',
                'func','returnStatement','return','breakStatement','comment',
                'augAssign','classStatement','class','dotAccess', 'importStatement',
                'import', 'kwargs','keyVal','keyVals','forTarget', 'delStatement',
                'delete', 'asStatement'}:
            phrase += t['token']
        else:
            raise Exception(f'Cannot convert the token {t["token"]} to a word')
        phrase += ' '
    return phrase[:-1]

def reduceToken(tokens):
    ''' Find patterns that can be reduced to a single token
        and return the reduced list of tokens
    '''
    global parsePhrase
    def reduce():
        for pattern in patterns:
            for i in range(len(tokenList)):
                if pattern == tuple(tokenList[i:i+len(pattern)]):
                    debug(pattern)
                    result = reduceToken(patterns[pattern](i+1,tokens))
                    if result == 'continue':
                        continue
                    else:
                        return result

    if tokens == 'continue':
        return 'continue'
    tokenList = [ token['token'] for token in tokens if not token['token'] == 'indent' ]
    parsePhrase = token2word(tokens)
    debug(parsePhrase)
    reducedTokens = reduce()
    if reducedTokens:
        tokens = reducedTokens

    # No patterns were found, reduced to maximum
    if len(tokens) > 2: #indent reducedToken (beginBlock)
        if not 'symbol' in tokens[0]:
            if 'indent' in tokens[0] and not 'symbol' in tokens[1]:
                showError(f'SyntaxError')
    return tokens

def assembly(tokens, block=None, modifier=None):
    ''' Match the given list of tokens with the corresponding '''
    ''' grammar and return a struct with its properties '''
    if not block == None:
        if not 'block' in tokens[1]:
            tokens[1]['block'] = block
            return tokens
        else:
            showError('Not expecting an ifBlock here...')
    elif not modifier == None:
        if modifier[1]['token'] == 'elifStatement':
            if not 'elifs' in tokens[1]:
                tokens[1]['elifs'] = []
            modifier = assembly(modifier)
            tokens[1]['elifs'].append({'expr':modifier['expr'], 'elifBlock':modifier['block']})
            return tokens
        elif modifier[1]['token'] == 'elseStatement':
            if not 'else' in tokens[1]:
                tokens[1]['else'] = modifier[1]['block']
                return tokens
            else:
                showError('Multiple else statements is not permitted')
        else:
            showError(f"Not implemented modifier handling for {modifier[1]['token']}")
                
    else:
        reduced = reduceToken(tokens)
        if len(reduced) > 1:
            struct = reduced[1]
            struct['opcode'] = struct['token']
            return struct

def showError(error):
    global currentLine, lineNumber, currentFilename
    msg = f'''


    Ops!! This is a syntax error or a parser error.
    Common causes: Missing "," ")" "}}"
    {error}
    This happened in line {currentFilename}:{lineNumber}.
    Last parsed line is "\n
    {currentLine}\n"
    Last Parse attempt was:\n "{parsePhrase}"
    '''
    raise SyntaxError(msg)

# Load grammar
import os
with open(f'{os.path.dirname(__file__)}/grammar/generatedGrammar.py') as g:
    exec(g.read())

