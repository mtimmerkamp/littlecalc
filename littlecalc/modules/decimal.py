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

import math
import decimal
from littlecalc.core import Module, NumericConverter, operation


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


def increase_precision(add=5):
    """
    Increase decimal precision before calculation and round result back to
    original precision. This function returns a decorating function.

    In the following examlpe::

        @increase_precision(add=10)
        def sin(x):
            # ... calculate result ...
            return result

    ``result`` is calculated with an additional precision of 10 digits. But
    before this result is passed to the caller, it is rounded back to original
    precision.
    """
    def decorating_function(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with decimal.localcontext() as ctx:
                ctx.prec += add  # increase precision for intermediate steps

                result = func(*args, **kwargs)

            return +result  # round back to previous precision

        return wrapper

    return decorating_function


class DecimalModule(Module):

    def __init__(self):
        super().__init__('decimal')

    def load_module(self, calc):
        super().load_module(calc)

        self.calc.register_numeric_type(DecimalConverter)

    def unload_module(self):
        self.calc.deregister_numeric_type(DecimalConverter)

        super().unload_module()

    @operation('prec', type='calc')
    def prec(self, calc):
        if calc.input_stream.has_next():
            try:
                new_prec = int(calc.input_stream.peek())
                calc.input_stream.pop()
            except ValueError:
                # TODO: raise error
                return

        context = decimal.getcontext()
        context.prec = new_prec

    @operation('prec?', type='calc')
    def prec_show(self, calc):
        calc.output('current precision: {}'.format(decimal.getcontext().prec))

    # basic mathematical operations

    @operation('add', aliases=['+'], type='stack', arg_count=2, add_plain=True)
    def add(x, y):
        return y + x

    @operation('sub', aliases=['-'], type='stack', arg_count=2, add_plain=True)
    def sub(x, y):
        return y - x

    @operation('mul', aliases=['*'], type='stack', arg_count=2, add_plain=True)
    def mul(x, y):
        return y * x

    @operation('div', aliases=['/'], type='stack', arg_count=2, add_plain=True)
    def div(x, y):
        return y / x

    @operation('inv', type='stack', arg_count=1, add_plain=True)
    def inv(x):
        return 1 / x

    @operation('sqrt', type='stack', arg_count=1, add_plain=True)
    def sqrt(x):
        return x.sqrt()

    @operation('sqr', aliases=['^2'], type='stack', arg_count=1,
               add_plain=True)
    def sqr(x):
        return x * x

    @operation('exp', type='stack', arg_count=1, add_plain=True)
    def exp(x):
        return x.exp()

    @operation('ln', type='stack', arg_count=1, add_plain=True)
    def ln(x):
        return x.ln()

    @operation('log10', aliases=['lg'], type='stack', arg_count=1,
               add_plain=True)
    def log10(x):
        return x.log10()

    @operation('pow', aliases=['**', '^'], type='stack', arg_count=2,
               add_plain=True)
    def power(x, y):
        return y ** x

    @operation('root', type='stack', arg_count=2, add_plain=True)
    def root(x, y):
        """Xth root of Y."""
        return y ** (1 / x)

    @operation('log', type='stack', arg_count=2, add_plain=True)
    @increase_precision(5)
    def log(x, y):
        return y.log10() / x.log10()  # log_x(y)

    @operation('abs', type='stack', arg_count=1, add_plain=True)
    def abs(x):
        return abs(x)

    @operation('floor', type='stack', arg_count=1, add_plain=True)
    def floor(x):
        return DecimalConverter.to_numeric(math.floor(x))

    @operation('ceil', type='stack', arg_count=1, add_plain=True)
    def ceil(x):
        return DecimalConverter.to_numeric(math.ceil(x))

    @operation('min', type='stack', arg_count=2, add_plain=True)
    def min(x, y):
        return min(x, y)

    @operation('max', type='stack', arg_count=2, add_plain=True)
    def max(x, y):
        return max(x, y)

    # trigonometric functions

    @operation('sin', type='stack', arg_count=1, add_plain=True)
    def sin(x):
        return _sin(x)

    @operation('cos', type='stack', arg_count=1, add_plain=True)
    def cos(x):
        return _cos(x)

    @operation('tan', type='stack', arg_count=1, add_plain=True)
    def tan(x):
        return _tan(x)

    @operation('cot', type='stack', arg_count=1, add_plain=True)
    def cot(x):
        return _cot(x)

    @operation('arctan', type='stack', arg_count=1, add_plain=True)
    def arctan(x):
        return _arctan(x)

    @operation('arccot', type='stack', arg_count=1, add_plain=True)
    def arccot(x):
        return _arccot(x)

    @operation('arcsin', type='stack', arg_count=1, add_plain=True)
    def arcsin(x):
        return _arcsin(x)

    @operation('arccos', type='stack', arg_count=1, add_plain=True)
    def arccos(x):
        return _arccos(x)

    @operation('sinh', type='stack', arg_count=1, add_plain=True)
    def sinh(x):
        return (x.exp() - (-x).exp()) / 2

    @operation('cosh', type='stack', arg_count=1, add_plain=True)
    def cosh(x):
        return (x.exp() + (-x).exp()) / 2

    @operation('tanh', type='stack', arg_count=1, add_plain=True)
    @increase_precision(5)
    def tanh(x):
        return DecimalModule.sinh(x) / DecimalModule.cosh(x)

    @operation('coth', type='stack', arg_count=1, add_plain=True)
    @increase_precision(5)
    def coth(x):
        return DecimalModule.cosh(x) / DecimalModule.sinh(x)

    @operation('arcsinh', type='stack', arg_count=1, add_plain=True)
    @increase_precision(5)
    def arcsinh(x):
        return (x + DecimalModule.sqrt(x**2 + 1)).ln()

    @operation('arccosh', type='stack', arg_count=1, add_plain=True)
    @increase_precision(5)
    def arccosh(x):
        return (x + DecimalModule.sqrt(x**2 - 1)).ln()

    @operation('arctanh', type='stack', arg_count=1, add_plain=True)
    @increase_precision(5)
    def arctanh(x):
        return ((1 + x) / (1 - x)).ln() / 2

    @operation('arccoth', type='stack', arg_count=1, add_plain=True)
    @increase_precision(5)
    def arccoth(x):
        return ((x + 1) / (x - 1)).ln() / 2


def compute_to_precision(init_factor, step_factor):
    """
    Returns a decorator which helps to compute a function's result to
    current precision. It increases the calculation precision by a factor
    ``step_factor`` until two consecutive calculations return the same result
    (that is rounded to the externally defined current precision).

    Before the first calculation starts, the calculation precision is
    multiplied by ``init_factor`` and rounded up, all following increases of
    the precision use ``init_factor``. ``init_factor`` must be greater
    than 0 and ``init_factor`` must be greater than 1.
    """
    if init_factor <= 0:
        raise ValueError('init_factor must be greater than 0')
    if step_factor < 1:
        raise ValueError('step_factor must be greater than 1')

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # this ensures that the loop runs at least two times
            result = None
            last_result = None

            current_prec = decimal.getcontext().prec
            # additional precision for intermediate steps
            # and ensure that ensure that the initial precision is at least 1
            next_prec = math.ceil(max(current_prec, 1) * init_factor)

            while last_result is None or result != last_result:
                last_result = result
                with decimal.localcontext() as ctx:
                    ctx.prec = next_prec

                    # calculate the actual result
                    result = func(*args, **kwargs)

                    next_prec = math.ceil(next_prec * step_factor)

                result = +result  # round back to previous precision
            return result

        return wrapper
    return decorator


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


@increase_precision(5)
def _sin(x):
    """
    Calculate ``sin(x)`` using the Taylor series:
        \sin(x) =
            \sum_{n=0}^{\infinity} (-1)^n \frac{ x^{2n + 1} }{ (2n + 1)! }
    """

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
    return s


@increase_precision(5)
def _cos(x):
    """
    Calculate ``cos(x)`` using the Taylor series:
        \cos(x) = \sum_{n=0}^{\infinity} (-1)^n \frac{ x^{2n} }{ (2n)! }
    """

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
    return s


# @compute_to_precision(1, 1.1)
@increase_precision(5)
def _tan(x):
    """
    Calculate ``tan(x)`` using:
        \tan(x) = \frac{ \sin(x) }{ \cos(x) }
    """
    return _sin(x) / _cos(x)


# @compute_to_precision(1, 1.1)
@increase_precision(5)
def _cot(x):
    """
    Calculate ``cot(x)`` using:
        \cot(x) = \frac{ \cos(x) }{ \sin(x) }
    """
    return _cos(x) / _sin(x)


@increase_precision(5)
def _arctan(x):
    """
    Calculate ``arctan(x)`` using:
        \arctan(x) = \sum_{k=0}^{\infinity} (-1)^k \frac{ x^{2k+1} }{ 2k + 1 }

    This series converges for |x| < 1, to support |x| >= 1 the following is
    used:
        \arctan(x) = 2 \arctan \frac{ x }{ x + \sqrt{ 1 + x^2 } }
    """
    if abs(x) >= 0.9:  # improve convergence for |x| ~ 1
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

    return +s


@increase_precision(5)
def _arccot(x):
    """
    Calculate ``arccot(x)`` using:
        \arccot(x) = \frac{ \pi }{ 2 } - \arctan(x)
    """
    pi = _calc_pi()
    return pi / 2 - _arctan(x)


@increase_precision(5)
def _arcsin(x):
    """
    Calculate ``arcsin(x)`` using:
        \arcsin(x) = \sgn(x) \arctan \sqrt{ \frac{ x^2 }{ 1 - x^2 } }
    for |x| < 1 and

        \arcsin(|x| = 1) = \sgn(x) \frac{ \pi }{ 2 }
    for |x| = 1.
    """
    sgn = -1 if x < 0 else 1
    if x == 1:
        pi = _calc_pi()

        result = sgn * pi / 2
    else:
        _0p5 = x / x / 2
        arg = (x**2 / (1 - x**2))**_0p5

        result = sgn * _arctan(arg)

    return result


@increase_precision(5)
def _arccos(x):
    """
    Calculate ``arccos(x)`` using:
        \arccos(x) = \frac{ \pi }{ 2 } - \arcsin(x)
    """
    pi = _calc_pi()
    return pi / 2 - _arcsin(x)


def get_modules(calc):
    return [DecimalModule()]
