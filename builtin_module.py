from littlecalc import Module, Numeric, CalculatorError
import decimal


class DecimalNumeric(Numeric):

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

        calc.register_numeric_type(DecimalNumeric)

    def unload_module(self, calc):
        super().unload_module(calc)

        calc.unregister_numeric_type(DecimalNumeric)


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

