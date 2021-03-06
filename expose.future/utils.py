"""
Decorators for exposing function arguments / returns
"""

from io import StringIO
import sys
import math
import functools   #, pprint




#TODO: unit tests!!!

#FIXME: you don't really need nested classes here.  since it is a module, you can access each
#function as a module attribute.....

# ====================================================================================================
def go_deep(func, args=(), kws=None):
    ''''''
    kws = kws or {}
    while isinstance(func, functools.partial):
        kws.update(func.keywords)
        args += func.args
        func = func.func
    return func, args, kws


def get_func_repr(func, fargs, fkw, verbosity=1, **kws):
    '''Get func repr in pretty format'''
    # TODO: checkout inspect.signature
    # TODO: update docstring
    # FIXME: works really terribly with arguments that format as multiline str... (indents etc...)

    shwmod = kws.get('show_module', bool(verbosity))
    shwdflt = kws.get('show_default', bool(verbosity))
    kwad = kws.get('kws_as_dict', bool(verbosity))

    #extract info for partial functions
    if isinstance(func, functools.partial):
        func, fargs, fkw = go_deep(func, fargs, fkw)

    # get display name
    fname = func.__name__  # FIXME:  does not work with classmethods
    module = getattr(func, '__module__', '') if shwmod else ''
    fname = '.'.join(filter(None, (module, fname)))

    code = func.__code__

    # Create a list of function argument strings
    arg_names = code.co_varnames[:code.co_argcount]     # co_varnames also contains local variables, we ignore those
    arg_vals = fargs[:len(arg_names)]                   # passed arguments
    if shwdflt:
        defaults = func.__defaults__ or ()
        arg_vals = arg_vals + defaults[len(defaults) - (code.co_argcount - len(arg_vals)):]

    name_value_pairs = list(zip(arg_names, arg_vals))       #NOTE: may be empty list

    if fkw and not kwad:
        name_value_pairs.extend(list(fkw.items()))

    args = fargs[len(arg_names):]
    if args:
        name_value_pairs.append(('args', args))

    if verbosity == 0:
        j = ', '
        lead_white = [0] * len(name_value_pairs)
        trail_white = 0
    elif verbosity == 1:
        # Adjust leading whitespace for pretty formatting
        j = ',\n'
        lead_white = [1] + [len(fname) + 1] * (len(name_value_pairs) - 1)
        trail_white = 0
        if len(name_value_pairs):
            trail_white = int(math.ceil(max(len(p[0]) for p in name_value_pairs) / 8) * 8)

    pars = j.join(
        ' ' * lead_white[i] + '{0[0]:<{1}}={0[1]}'.format(p, trail_white)
        for i, p in enumerate(name_value_pairs))
    pr = '{fname}({pars})'.format(fname=fname, pars=pars)

    return pr

# ====================================================================================================
# def get_func_repr(func, fargs, fkw={}, verbosity=0):
#
#     fname = func.__name__       #FIXME:  does not work with classmethods
#     code = func.__code__
#
#     #Create a list of function argument strings
#     nco = code.co_argcount              #number of arguments (not including * or ** args)
#     arg_names = code.co_varnames[:nco]  #tuple of names of arguments (exclude local variables)
#     arg_vals = fargs[:len(arg_names)]   #
#     defaults = func.__defaults__    or  ()
#     arg_vals += defaults[len(defaults) - (nco - len(arg_vals)):]
#
#     params = list(zip(arg_names, arg_vals))
#     args = fargs[len(arg_names):]
#
#     if args:
#         params.append(('args', args))
#     if fkw:
#         params.append(('kwargs', pprint.pformat(fkw, indent=3)))
#
#         #print('HELLOOOOOOO!!!')
#         #print(pprint.pformat(fkw))
#         #print('\n\n')
#
#     if verbosity==0:
#         j = ', '
#     elif verbosity==1:
#         j = ',\n'
#
#     #TODO: use pprint for kwargs.....
#
#     #Adjust leading whitespace for pretty formatting
#     #TODO: spread option
#     lead_white = [0] + [len(fname)+1] * (len(params)-1)
#     trail_white = int(np.ceil(max(len(p[0]) for p in params)/8)*8)
#     pars = j.join(' '*lead_white[i] + \
#                   '{0[0]:<{1}}= {0[1]}'.format(p, trail_white)
#                         for i, p in enumerate(params))
#     pr = '{fname}({pars})'.format(fname=fname, pars=pars)
#
#     return pr

#pretty_signature_str = get_func_repr




#****************************************************************************************************
class expose():
    #TODO: OO
    #TODO: check Ipython traceback formatter?
    #TODO: Use superstring!!
    '''
    class that contains decorators for printing function arguments / content / returns
    '''
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def args(pre='', post='\n', verbosity=1):
        '''
        Decorator to print function call details - parameters names and effective values
        optional arguments specify stuff to print before and after, as well as verbosity level.

        Example
        -------
        In [43]: @expose.args()
            ...: def foo(a, b, c, **kw):
            ...:     return a
            ...:
            ...: foo('aaa', 42, id, gr=8, bar=...)

        prints:
        foo( a       = aaa,
             b       = 42,
             c       = <built-in function id>,
             kwargs  = {'bar': Ellipsis, 'gr': 8} )

        Out[43]: 'aaa'
        '''
        #====================================================================================================
        def actualDecorator(func):

            @functools.wraps(func)          #TODO: this wrapper as an importable function...
            def wrapper(*fargs, **fkw):

                frep = get_func_repr(func, fargs, fkw, verbosity)

                print(pre)
                print(frep)
                print(post)
                sys.stdout.flush()

                return func(*fargs, **fkw)

            return wrapper

        return actualDecorator

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def returns():
        '''Decorator to print function return details'''
        def actualDecorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kw):
                r = func(*args, **kw)
                print( 'RETURNING!' )
                print( r )
                return r
            return wrapper
        return actualDecorator

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def suppress(func):
        '''Suppress all print statements in a function call'''
        @functools.wraps(func)
        def wrapper(*args, **kws):
            #shadow stdout temporarily
            actualstdout = sys.stdout
            sys.stdout = StringIO()

            #call the actual function
            r = func(*args, **kws)

            #restore stdout
            sys.stdout = actualstdout
            sys.stdout.flush()

            return r

        return wrapper

#alias
suppress_print = expose.suppress



