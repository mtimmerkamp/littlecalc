# little-calc.
# Copyright (C) 2017  Maximilian Timmerkamp

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import functools

import decimal
from littlecalc import Module, NumericConverter, CalculatorError


class DecimalConverter(NumericConverter):

    @classmethod
    def is_numeric(cls, word):
        try:
            value = decimal.Decimal(word)
            return True
        except decimal.InvalidOperation:
            return False

    @classmethod
    def to_numeric(cls, word):
        return decimal.Decimal(word)


class BuiltinModule(Module):

    def __init__(self, name):
        super().__init__(name)

    def load_module(self, calc):
        super().load_module(calc)

        calc.register_numeric_type(DecimalConverter)

    def unload_module(self, calc):
        super().unload_module(calc)

        calc.unregister_numeric_type(DecimalConverter)


module = BuiltinModule('builtin')


# special operations (e.g. stack)

@module.add_operation('sto')
def sto(module, calc):
    if calc.input_stream.has_next():
        dest = calc.input_stream.pop()
    else:
        raise CalculatorError('argument missing')
    value = calc.stack.pop()

    calc.storage[dest] = value


@module.add_operation('rcl')
def rcl(module, calc):
    if calc.input_stream.has_next():
        dest = calc.input_stream.pop()
    else:
        raise CalculatorError('argument missing')
    value = calc.storage[dest]

    calc.stack.push(value)


# basic mathematical operations

def simple_arith_operation(arg_count):
    """Create a decorator for a simple arithmetic function with one
    result, consuming ``arg_count`` topmost values from stack.

    Pop ``arg_count`` values from stack (see Stack.pop) and call
    the function with these values as parameters. The return value
    is pushed onto the stack.

    The following function::

        @simple_arith_operation(2)
        def add(module, calc, x, y):
            return y + x

    is therefore equivalent to::

        @simple_arith_operation(2)
        def add(module, calc):
            x, y = calc.stack.pop(2)
            result = y + x
            calc.stack.push(result)
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(module, calc):
            values = calc.stack.pop(arg_count)
            result = f(module, calc, *values)
            calc.stack.push(result)
        return wrapper
    return decorator


@module.add_operation('add', aliases=['+'])
@simple_arith_operation(2)
def add(module, calc, x, y):
    return y + x


@module.add_operation('sub', aliases=['-'])
@simple_arith_operation(2)
def sub(module, calc, x, y):
    return y - x


@module.add_operation('mul', aliases=['*'])
@simple_arith_operation(2)
def mul(module, calc, x, y):
    return y * x


@module.add_operation('div', aliases=['/'])
@simple_arith_operation(2)
def div(module, calc, x, y):
    return y / x


@module.add_operation('inv')
@simple_arith_operation(1)
def inv(module, calc, x):
    return 1 / x


@module.add_operation('sqrt')
@simple_arith_operation(1)
def sqrt(module, calc, x):
    return x.sqrt()


@module.add_operation('sqr', aliases=['^2'])
@simple_arith_operation(1)
def sqr(module, calc, x):
    return x * x


@module.add_operation('exp')
@simple_arith_operation(1)
def exp(module, calc, x):
    return x.exp()


@module.add_operation('ln')
@simple_arith_operation(1)
def ln(module, calc, x):
    return x.ln()


@module.add_operation('log10', aliases=['lg'])
@simple_arith_operation(1)
def log10(module, calc, x):
    return x.log10()


@module.add_operation('pow', aliases=['**', '^'])
@simple_arith_operation(2)
def pow(module, calc, x, y):
    return x ** y


@module.add_operation('log')
@simple_arith_operation(2)
def log(module, calc, x, y):
    with decimal.localcontext() as ctx:
        ctx.prec += 5  # increase precision for intermediate steps
        result = y.log10() / x.log10()
    return +result  # round back to previous precision


def get_modules(calc):
    return [module]
