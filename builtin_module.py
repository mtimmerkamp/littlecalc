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

from littlecalc import Module, NumericConverter, CalculatorError
import decimal


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

@module.add_operation('add')
def add(module, calc):
    x, y = calc.stack.pop(2)
    calc.stack.push(y + x)


@module.add_operation('sub')
def sub(module, calc):
    x, y = calc.stack.pop(2)
    calc.stack.push(y - x)


@module.add_operation('mul')
def mul(module, calc):
    x, y = calc.stack.pop(2)
    calc.stack.push(y * x)


@module.add_operation('div')
def div(module, calc):
    x, y = calc.stack.pop(2)
    calc.stack.push(y / x)


module.add_alias('+', 'add')
module.add_alias('-', 'sub')
module.add_alias('*', 'mul')
module.add_alias('/', 'div')


def get_modules(calc):
    return [module]

