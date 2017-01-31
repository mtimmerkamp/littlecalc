# littlecalc
# Copyright (C) 2017  Maximilian Timmerkamp
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import functools

import decimal
from littlecalc.core import Module, NumericConverter, CalculatorError


class DecimalConverter(NumericConverter):

    @classmethod
    def is_numeric(cls, word):
        try:
            _ = cls.to_numeric(word)
            return True
        except decimal.InvalidOperation:
            return False

    @classmethod
    def to_numeric(cls, word):
        return decimal.Decimal(word)


class DecimalModule(Module):

    def __init__(self):
        super().__init__('decimal')

    def load_module(self, calculator):
        super().load_module(calculator)

        calculator.register_numeric_type(DecimalConverter)

    def unload_module(self, calculator):
        super().unload_module(calculator)

        calculator.unregister_numeric_type(DecimalConverter)


module = DecimalModule()


# special operations (e.g. stack)

@module.add_operation('store', aliases=['sto'])
def store(calc):
    if calc.input_stream.has_next():
        destination = calc.input_stream.pop()
    else:
        raise CalculatorError('argument missing')
    value = calc.stack.pop()

    calc.storage[destination] = value


@module.add_operation('recall', aliases=['rcl'])
def recall(calc):
    if calc.input_stream.has_next():
        src = calc.input_stream.pop()
    else:
        raise CalculatorError('argument missing')
    value = calc.storage[src]

    calc.stack.push(value)


@module.add_operation('clear', aliases=['clr'])
def clear_stack(calc):
    """Clears stack."""
    calc.stack.clear()


@module.add_operation('clearall')
def clear_all(calc):
    """Clears stack and variable storage."""
    calc.stack.clear()
    calc.storage.clear()


# basic mathematical operations

def simple_arith_operation(arg_count):
    """Create a decorator for a simple arithmetic function with one
    result, consuming ``arg_count`` topmost values from stack.

    Pop ``arg_count`` values from stack (see Stack.pop) and call
    the function with these values as parameters. The return value
    is pushed onto the stack.

    The following function::

        @simple_arith_operation(2)
        def add(x, y):
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
        def wrapper(calc):
            values = calc.stack.pop(arg_count)
            result = f(*values)
            calc.stack.push(result)
        return wrapper
    return decorator


@module.add_operation('add', aliases=['+'])
@simple_arith_operation(2)
def add(x, y):
    return y + x


@module.add_operation('sub', aliases=['-'])
@simple_arith_operation(2)
def sub(x, y):
    return y - x


@module.add_operation('mul', aliases=['*'])
@simple_arith_operation(2)
def mul(x, y):
    return y * x


@module.add_operation('div', aliases=['/'])
@simple_arith_operation(2)
def div(x, y):
    return y / x


@module.add_operation('inv')
@simple_arith_operation(1)
def inv(x):
    return 1 / x


@module.add_operation('sqrt')
@simple_arith_operation(1)
def sqrt(x):
    return x.sqrt()


@module.add_operation('sqr', aliases=['^2'])
@simple_arith_operation(1)
def sqr(x):
    return x * x


@module.add_operation('exp')
@simple_arith_operation(1)
def exp(x):
    return x.exp()


@module.add_operation('ln')
@simple_arith_operation(1)
def ln(x):
    return x.ln()


@module.add_operation('log10', aliases=['lg'])
@simple_arith_operation(1)
def log10(x):
    return x.log10()


@module.add_operation('pow', aliases=['**', '^'])
@simple_arith_operation(2)
def power(x, y):
    return y ** x


@module.add_operation('log')
@simple_arith_operation(2)
def log(x, y):
    with decimal.localcontext() as ctx:
        ctx.prec += 5  # increase precision for intermediate steps
        result = y.log10() / x.log10()  # log_x(y)
    return +result  # round back to previous precision


def get_modules(calc):
    return [module]
