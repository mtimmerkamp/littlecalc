# little-calc
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

from littlecalc import Module, CalculatorError
from decimal import localcontext


class ConstantError(CalculatorError):
    pass


class UnknownConstantError(ConstantError):

    def __init__(self, constant_id):
        super().__init__('No such constant: "{}"'.format(constant_id))


class ConstantCalculationError(ConstantError):
    pass


class ConstantsModule(Module):

    def __init__(self):
        super().__init__('constants')

        self.descriptions = {}
        """Mapping a constant's id to a short description."""

        self.fixed_constants = {}
        """Mapping a constant's id to its value. Only for constants
        which are known to a fixed precision and therefore
        independent of the current calculator precision."""

        self.constant_calculators = {}
        """Mapping a constant's id to a function that can calculate
        the constant up to the current precision of the calculator."""

    def get(self, constant_id):
        """Returns a numeric value for the requested constant. An
        ``UnknownConstantError`` is raised if an unknown constant
        id is passed. If an error occurs while calculating a
        constant, a ``ConstantCalculationError`` is raised.

        The requested constant will be returned as by
        ``Calculator.to_numeric``.

        If there is a function available to calculate the requested
        constant, it will be used instead of a stored fixed value.
        """
        try:
            func = self.constant_calculators[constant_id]
        except KeyError:
            try:
                value = self.fixed_constants[constant_id]
            except KeyError:
                raise UnknownConstantError(constant_id)
            return self.calculator.to_numeric(value)

        try:
            return func(self.calculator)
        except Exception as err:
            raise ConstantCalculationError(
                'Cannot calculate constant: "{}"'.format(constant_id)
            ) from err

    def __getitem__(self, item):
        return self.get(constant_id=item)

    def __contains__(self, item):
        return item in self.descriptions

    def __iter__(self):
        return iter(self.descriptions)

    def add(self, constant_id, description, value=None, func=None):
        """Add a constant to constant store. ``constant_id`` and
        ``description`` are required as well as one of ``value``
        and ``func``. ``value`` is a string to be converted
        by ``Calculator.to_numeric``, while ``func`` is a function
        that takes a calculator object as parameter.

        If ``value`` is set, a fixed constant is created.
        If ``func`` is set, the function will be called each time the
        constant is requested to allow calculating the constant to the
        current calculator precision.
        """
        if value is None and func is None:
            raise ValueError('value and func must not both be None')
        elif value is not None and func is not None:
            raise ValueError('value and func must not both be set')

        self.descriptions[constant_id] = description
        if value is not None:
            self.fixed_constants[constant_id] = value
        else:
            self.constant_calculators[constant_id] = func


def calc_e(calc):
    to_num = calc.to_numeric
    with localcontext() as ctx:
        ctx.prec += 5
        i, fact, num = 0, 1, to_num('1.0')
        lasts, s = to_num('0'), to_num('1.0')
        while s != lasts:
            lasts = s
            i += 1
            fact *= i
            # num *= 1  # calculation of e^1
            s += num / fact
    return +s  # rounding back to original precision


def calc_pi(calc):
    to_num = calc.to_numeric
    with localcontext() as ctx:
        ctx.prec += 5  # increase precision for intermediate steps

        const_0p5 = to_num('0.5')

        # Gauss-Legendre algorithm
        an, bn, tn, pn = to_num(1), 1/to_num(2)**const_0p5, 1/to_num(4), 1
        v, lastv = 0, 1
        while v != lastv:
            a, b, t, p = an, bn, tn, pn

            an = (a + b) / 2
            bn = (a * b)**const_0p5
            tn = t - p * (a - an)**2
            pn = 2 * p

            lastv = v
            v = (an + bn)**2 / (4 * tn)

    return +v  # round back to previous precision


def add_default_constants(module):
    module.add('e', 'Euler\'s number', func=calc_e)
    module.add('pi', 'ratio of a circle\'s circumference to its diameter',
               func=calc_pi)


module = ConstantsModule()
add_default_constants(module)


@module.add_operation('const')
def const(module, calc):
    if calc.input_stream.has_next():
        constant_id = calc.input_stream.pop()
    else:
        raise CalculatorError('argument missing: constant id')

    try:
        value = module.get(constant_id)
    except ConstantError as err:
        import traceback
        # TODO: add error handling/output to Calculator
        print(''.join(traceback.format_exception(type(err), err, None)))
    else:
        calc.stack.push(value)


def get_modules(calc):
    return [module]
