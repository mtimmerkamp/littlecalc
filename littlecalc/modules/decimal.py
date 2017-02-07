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
            cls.to_numeric(word)
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

        def add(calc):
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


def _calc_pi(cache={}):
    current_context = decimal.getcontext()
    if current_context.prec in cache:
        return cache[current_context.prec]

    D = decimal.Decimal
    with decimal.localcontext() as ctx:
        ctx.prec += 5  # increase precision for intermediate steps

        const_0p5 = D('0.5')

        # Gauss-Legendre algorithm
        an, bn, tn, pn = D(1), 1 / D(2)**const_0p5, 1 / D(4), 1
        v, lastv = 0, 1
        while v != lastv:
            a, b, t, p = an, bn, tn, pn

            an = (a + b) / 2
            bn = (a * b)**const_0p5
            tn = t - p * (a - an)**2
            pn = 2 * p

            lastv = v
            v = (an + bn)**2 / (4 * tn)
    v = +v  # round back to previous precision

    cache[current_context.prec] = v
    return v


def _sin(x):
    """
    Calculate ``sin(x)`` using the Taylor series:
        \sin(x) =
            \sum_{n=0}^{\infinity} (-1)^n \frac{ x^{2n + 1} }{ (2n + 1)! }
    """
    with decimal.localcontext() as ctx:
        ctx.prec += 5  # additional precision for intermediate steps

        pi = _calc_pi()
        x = x % (2 * pi)  # cos works best for small x

        s, lasts = x, 0
        i, num, fac, sign = 1, x, 1, 1

        while s != lasts:
            lasts = s

            i += 2
            fac *= i * (i - 1)
            num *= x * x
            sign *= -1

            s += num / fac * sign
    return +s  # round back to previous precision


@module.add_operation('sin')
@simple_arith_operation(1)
def sin(x):
    return _sin(x)


def _cos(x):
    """
    Calculate ``cos(x)`` using the Taylor series:
        \cos(x) = \sum_{n=0}^{\infinity} (-1)^n \frac{ x^{2n} }{ (2n)! }
    """
    with decimal.localcontext() as ctx:
        ctx.prec += 5  # additional precision for intermediate steps

        pi = _calc_pi()
        x = x % (2 * pi)  # cos works best for small x

        s, lasts = 1, 0
        i, num, fac, sign = 0, 1, 1, 1

        while s != lasts:
            lasts = s

            i += 2
            fac *= i * (i - 1)
            num *= x * x
            sign *= -1

            s += num / fac * sign
    return +s  # round back to previous precision


@module.add_operation('cos')
@simple_arith_operation(1)
def cos(x):
    return _cos(x)


def _tan(x):
    """
    Calculate ``tan(x)`` using:
        \tan(x) = \frac{ \sin(x) }{ \cos(x) }
    """
    with decimal.localcontext() as ctx:
        ctx.prec *= 2  # additional precision for intermediate steps
        result = _sin(x) / _cos(x)
    return +result


@module.add_operation('tan')
@simple_arith_operation(1)
def tan(x):
    return _tan(x)


def _cot(x):
    """
    Calculate ``cot(x)`` using:
        \cot(x) = \frac{ \cos(x) }{ \sin(x) }
    """
    with decimal.localcontext() as ctx:
        ctx.prec *= 2  # additional precision for intermediate steps
        result = _cos(x) / _sin(x)
    return +result


@module.add_operation('cot')
@simple_arith_operation(1)
def cot(x):
    return _cot(x)


def _arctan(x):
    """
    Calculate ``arctan(x)`` using:
        \arctan(x) = \sum_{k=0}^{\infinity} (-1)^k \frac{ x^{2k+1} }{ 2k + 1 }

    This series converges for |x| < 1, to support |x| > 1 the following is
    used:
        \arctan(x) = 2 \arctan \frac{ x }{ x + \sqrt{ 1 + x^2 } }
    """
    with decimal.localcontext() as ctx:
        ctx.prec += 5  # additional precision for intermediate steps

        if abs(x) >= 1:
            _0p5 = x / x / 2
            x = x / (1 + (1 + x**2)**_0p5)
            s = 2 * _arctan(x)
        else:
            s = x
            lasts = 0
            num = x
            sign = 1
            k = 0

            while s != lasts:
                lasts = s
                k += 1

                sign *= -1
                num *= x * x

                s += sign * num / (2 * k + 1)
    return +s  # round back to previous precision


@module.add_operation('arctan')
@simple_arith_operation(1)
def arctan(x):
    return _arctan(x)


def _arccot(x):
    """
    Calculate ``arccot(x)`` using:
        \arccot(x) = \frac{ \pi }{ 2 } - \arctan(x)
    """
    with decimal.localcontext() as ctx:
        ctx.prec += 5  # additional precision for intermediate steps

        pi = _calc_pi()
        result = pi / 2 - _arctan(x)
    return + result  # round back to previous precision


@module.add_operation('arccot')
@simple_arith_operation(1)
def arccot(x):
    return _arccot(x)


def _arcsin(x):
    """
    Calculate ``arcsin(x)`` using:
        \arcsin(x) = \sgn(x) \arctan \sqrt{ \frac{ x^2 }{ 1 - x^2 } }
    for |x| < 1 and

        \arcsin(|x| = 1) = \sgn(x) \frac{ \pi }{ 2 }
    for |x| = 1.
    """
    with decimal.localcontext() as ctx:
        ctx.prec += 5  # additional precision for intermediate steps

        sgn = -1 if x < 0 else 1
        if x == 1:
            pi = _calc_pi()

            result = sgn * pi / 2
        else:
            _0p5 = x / x / 2
            arg = (x**2 / (1 - x**2))**_0p5

            result = sgn * _arctan(arg)
    return +result  # round back to previous precision


@module.add_operation('arcsin')
@simple_arith_operation(1)
def arcsin(x):
    return _arcsin(x)


def _arccos(x):
    """
    Calculate ``arccos(x)`` using:
        \arccos(x) = \frac{ \pi }{ 2 } - \arcsin(x)
    """
    with decimal.localcontext() as ctx:
        ctx.prec += 5  # additional precision for intermediate steps

        pi = _calc_pi()
        result = pi / 2 - _arcsin(x)
    return +result  # round back to previous precision


@module.add_operation('arccos')
@simple_arith_operation(1)
def arccos(x):
    return _arccos(x)


def get_modules(calc):
    return [module]
