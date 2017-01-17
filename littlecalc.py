#!/usr/bin/env python3
"""
This is a little calculator using reverse polish notation (RPN). It is meant
to be small in that it should be single file. However "external" modules
are allowed to provide additional features.


Idea:
user input is converted into a "stream", all functions can pull from this
stream or from the stack enabling operations like:
    sto a

where "sto" pulls one word from the stream to use it as a parameter.
"""


from collections import deque, ChainMap
import decimal


class CalculatorError(Exception):
    pass


class NoSuchOperation(CalculatorError):

    def __init__(self, name):
        super.__init__(self, 'no such operation: {}'.format(name))


class NoSuchAlias(CalculatorError):

    def __init__(self, name):
        super.__init__(self, 'no such alias: {}'.format(name))


class Module:

    def __init__(self, name, operations=None, aliases=None):
        self.name = name
        self.operations = {} if operations is None else operations
        self.aliases = {} if aliases is None else aliases

    def add_operation(self, name, operation):
        operation.name = name
        self.operations[name] = operation

    def add_alias(self, alias, operation_name):
        if operation_name in self.aliases:
            # TODO: Create proper error for this: Alias an alias
            raise CalculatorError('Aliasing an alias is not allowed.')

        self.aliases[alias] = operation_name

    def register(self, name):
        def wrapper(f):
            self.add_operation(name, f)
            return f
        return wrapper


class Calculator:

    def __init__(self):
        self.stack = deque()
        self.modules = []

        self.operations = ChainMap()
        self.aliases = ChainMap({})

    def load_module(self, module):
        self.modules.append(module)

        self.operations.maps.insert(0, module.operations)
        self.aliases.maps.insert(1, module.operations)  # first alias map is always user-defined.

    def unload_module(self, module):
        self.aliases.maps.remove(module.aliases)
        self.operations.maps.operations.remove(module.operations)

        self.modules.remove(module)

    def is_alias(self, alias):
        return alias in self.aliases

    def is_operation(self, op):
        return op in self.operations

    def resolve_alias(self, alias):
        try:
            return self.aliases[alias]
        except KeyError:
            raise NoSuchAlias(alias)

    def get_operation(self, name):
        try:
            return self.operations[name]
        except KeyError:
            raise NoSuchOperation(name)

    def do_operation(self, name):
        """Resolves aliases and """
        if name in self.aliases:
            name = self.resolve_alias(name)
        op = self.get_operation(name)

        op(self)

    def is_number(self, s):
        return s.isdigit()

    def convert_number(self, s):
        return decimal.Decimal(s)

    def parse_input(self, input_):
        input_stream = (word for word in input_.split())

        for word in input_stream:
            if self.is_number(word):
                x = self.convert_number(word)
                self.stack.append(x)
            elif self.is_operation(word) or self.is_alias(word):
                do_operation(word)
            else:
                print('UNKNOWN INPUT:', word)


def main():
    calc = Calculator()
    while True:
        user_input = input('>>> ')

        calc.parse_input(user_input)

if __name__ == '__main__':
    main()
