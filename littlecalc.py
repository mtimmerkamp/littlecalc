#!/usr/bin/env python3

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
import abc
import decimal
import importlib
import importlib.util


class CalculatorError(Exception):
    pass


class NoSuchOperation(CalculatorError):

    def __init__(self, name):
        super().__init__('no such operation: {}'.format(name))


class NotNumeric(CalculatorError):

    def __init__(self, word):
        super().__init__('word is not numeric: "{}"'.format(word))


class AliasingError(CalculatorError):
    pass


class NumericConverter(metaclass=abc.ABCMeta):

    @classmethod
    @abc.abstractmethod
    def is_numeric(cls, word: str) -> bool:
        return False

    @classmethod
    @abc.abstractmethod
    def convert_numeric(cls, word: str) -> object:
        return None


class Module:

    def __init__(self, name, operations=None, aliases=None):
        self.name = name
        self.calculator = None

        self.operations = operations or {}
        self.aliases = aliases or {}

    def add_operation(self, name, operation=None, aliases=None):
        """Add an operation to this module and add aliases (if requested).
        If ``operation`` is ``None``, a decorator function will be
        returned. That way it is possible to use a call of this function
        as decorator like::

            @module.add_operation('add')
            def add(module, calc):
                return 0

        where a new operation called ``add`` wildecimall be added to
        ``module`` as if::

            module.add_operation('add', add)

        was invoked.
        """
        if operation is None:  # use as decorator
            def decorator(func):
                return self.add_operation(name, func, aliases=aliases)
            return decorator
        else:
            operation.name = name
            self.operations[name] = operation

            if aliases is not None:
                for alias in aliases:
                    self.add_alias(alias, name)

            return operation

    def add_alias(self, alias, operation_name):
        """Add alias ``alias`` for operation ``operation_name``.
        If ``operation_name`` is an alias, it will be resolved to
        an operation.

        Note: There is no protection against cyclic aliases which
        will cause an infinite loop."""
        while operation_name in self.aliases:
            operation_name = self.aliases[operation_name]

        self.aliases[alias] = operation_name

    def load_module(self, calculator):
        """Called when ``calculator`` loads this module."""
        self.calculator = calculator

    def unload_module(self):
        """Called when this module is being unloaded."""
        self.calculator = None

    def is_executable(self, operation):
        """Returns whether the passed operation is executable by
        this module."""
        return operation in self.operations or operation in self.aliases

    def do_operation(self, operation):
        try:
            if operation in self.aliases:
                alias = self.aliases[operation]
                op = self.operations[alias]
            else:
                op = self.operations[operation]
        except KeyError:
            raise NoSuchOperation(operation)

        op(self, self.calculator)


class Stack:

    def __init__(self, stack=None):
        self.stack = deque(stack or [])

    def pop(self, count=None):
        """Return the last entry pushed onto the stack. If ``count``
        is an int, a list of the last ``count`` entries is returned,
        where the first item is the topmost entry on the stack."""
        if count is None:
            return self.stack.pop()
        elif isinstance(count, int):
            return [self.stack.pop() for _ in range(count)]
        else:
            raise ValueError('int or None required')

    def push(self, *values):
        """Push ``values`` to the stack. The last item of ``values``
        will be put on top of the stack."""
        for value in values:
            self.stack.append(value)

    def __str__(self):
        return str(self.stack)


class ConsumingInputStream:

    def __init__(self, iterable):
        self.stream = deque(iterable)

    def peek(self):
        return self.stream[0]

    def pop(self):
        return self.stream.popleft()

    def has_next(self):
        return len(self.stream) > 0

    def __len__(self):
        return len(self.stream)

    def __iter__(self):
        while True:
            try:
                value = self.pop()
                yield value
            except IndexError:
                raise StopIteration


class Calculator:

    def __init__(self):
        self.stack = Stack()
        self.storage = dict()

        self.input_stream = None

        self.modules = []
        self.numeric_types = []

    def load_module(self, module):
        module.load_module(self)
        self.modules.append(module)

    def unload_module(self, module):
        module.unload_module(self)
        self.modules.remove(module)

    def register_numeric_type(self, cls):
        self.numeric_types.append(cls)

    def deregister_numeric_type(self, cls):
        self.numeric_types.remove(cls)

    def is_numeric(self, word):
        for numeric_type in self.numeric_types:
            if numeric_type.is_numeric(word):
                return True
        return False

    def to_numeric(self, word):
        for numeric_type in self.numeric_types:
            if numeric_type.is_numeric(word):
                return numeric_type.to_numeric(word)
        raise NotNumeric(word)

    def is_executable(self, word):
        for module in self.modules:
            if module.is_executable(word):
                return True
        return False

    def get_module(self, operation):
        for module in self.modules:
            if module.is_executable(operation):
                return module
        raise NoSuchOperation(operation)

    def do_operation(self, name):
        """Invokes the desired operation."""
        module = self.get_module(name)
        module.do_operation(name)

    def convert_number(self, s):
        return decimal.Decimal(s)

    def parse_input(self, input_):
        self.input_stream = ConsumingInputStream(input_.split())

        for word in self.input_stream:
            if self.is_numeric(word):
                x = self.to_numeric(word)
                self.stack.push(x)
            elif self.is_executable(word):
                self.do_operation(word)
            else:
                print('UNKNOWN INPUT:', word)

        self.input_stream = None


def main():
    module_name = 'builtin_module'
    file_path = './builtin_module.py'

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    calc = Calculator()
    calc.load_module(module.get_modules(calc)[0])
    while True:
        user_input = input('>>> ')

        calc.parse_input(user_input)
        print(calc.stack)

if __name__ == '__main__':
    main()
