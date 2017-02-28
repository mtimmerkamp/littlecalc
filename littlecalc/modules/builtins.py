import sys
import traceback
from littlecalc.core import Module, CalculatorError, ModuleLoadError, operation


class BuiltinsModule(Module):

    def __init__(self):
        super().__init__('builtins')

    @operation('store', aliases=['sto'], type='plain')
    def store(calc, destination, value):
        calc.storage[destination] = value
    store.add('remote', pass_module=False)

    @store.add('calc')
    def store(self, calc):
        if calc.input_stream.has_next():
            destination = calc.input_stream.pop()
        else:
            raise CalculatorError('argument missing')
        value = calc.stack.pop()

        self.store(calc, destination, value)

    @operation('recall', aliases=['rcl'], type='plain')
    def recall(calc, source):
        value = calc.storage[source]
        calc.stack.push(value)
    recall.add('remote', pass_module=False)

    @recall.add('calc')
    def recall(self, calc):
        if calc.input_stream.has_next():
            source = calc.input_stream.pop()
        else:
            raise CalculatorError('argument missing')

        self.recall(calc, source)

    @operation('clear', aliases=['clr'], type='calc')
    def clear_stack(self, calc):
        """Clears stack."""
        calc.stack.clear()
    clear_stack.add('remote', from_type='calc')

    @operation('clearall', type='calc')
    def clear_all(self, calc):
        """Clears stack and variable storage."""
        calc.stack.clear()
        calc.storage.clear()
    clear_all.add('remote', from_type='calc')

    @operation('xchy', type='calc')
    def xchy(self, calc):
        """Exchange X and Y register."""
        if len(calc.stack) >= 2:
            x, y = calc.stack.pop(2)
            calc.stack.push(x, y)
    xchy.add('remote', from_type='calc')

    @operation('rolup', aliases=['rlu'], type='calc')
    def rolup(self, calc):
        calc.stack.rotate(-1)
    rolup.add('remote', from_type='calc')

    @operation('roldown', aliases=['rld'], type='calc')
    def roldown(self, calc):
        calc.stack.rotate(1)
    roldown.add('remote', from_type='calc')

    @operation('push', type='calc')
    def push(self, calc):
        try:
            value = calc.stack.peek()
        except IndexError:
            pass
        else:
            calc.stack.push(value)
    push.add('remote', from_type='calc')

    @operation('pop', type='calc')
    def pop(self, calc):
        try:
            calc.stack.pop()
        except IndexError:
            pass
    pop.add('remote', from_type='calc')

    @operation('lastx', type='calc')
    def lastx(self, calc):
        if calc.stack.lastx is not None:
            calc.stack.push(calc.stack.lastx)
    lastx.add('remote', from_type='calc')

    @operation('loadmod', type='calc')
    def loadmod(self, calc):
        if calc.input_stream.has_next():
            module_name = calc.input_stream.pop()
        else:
            raise CalculatorError('argument missing')

        try:
            calc.load_module_by_name(module_name)
        except ModuleLoadError as err:
            calc.output(
                'An error occurred loading module {!r}'.format(module_name))
            calc.output(traceback.format_exc())

    @operation('unloadmod', type='calc')
    def unloadmod(self, calc):
        if calc.input_stream.has_next():
            module_name = calc.input_stream.pop()
        else:
            raise CalculatorError('argument missing')
        calc.unload_module_by_name(module_name)


def get_modules(calc):
    return [BuiltinsModule()]
