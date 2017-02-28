#!/usr/bin/env python3

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


import abc
import functools
import importlib
import importlib.util
import traceback
from collections import deque


class CalculatorError(Exception):
    pass


class NoSuchOperation(CalculatorError):

    def __init__(self, name):
        super().__init__('no such operation: {!r}'.format(name))


class NotNumeric(CalculatorError):

    def __init__(self, word):
        super().__init__('word is not numeric: {!r}'.format(word))


class AliasingError(CalculatorError):
    pass


class ModuleLoadError(CalculatorError):
    pass


class NumericConverter(metaclass=abc.ABCMeta):

    @classmethod
    @abc.abstractmethod
    def is_numeric(cls, word: str) -> bool:
        return False

    @classmethod
    @abc.abstractmethod
    def to_numeric(cls, word: str) -> object:
        return None


def stack_op(func=None, arg_count=None, push_multiple=False):
    """Create a decorator for a simple arithmetic function with one result,
    consuming ``arg_count`` topmost values from stack.

    Pop ``arg_count`` values from stack (see Stack.pop) and call the function
    with these values as parameters. The return value is pushed onto the
    stack if ``push_multiple`` is False. If ``push_multiple`` is True, the
    decorated function is expected to return an iterable whose contents
    are pushed onto the stack. The first item of the iterable will be pushed
    first.

    The following function::

        @stack_op(2)
        def add(x, y):
            return y + x

    is therefore equivalent to::

        def add(module, calc):
            x, y = calc.stack.pop(2)
            result = y + x
            calc.stack.push(result)
    """
    if arg_count is None:
        raise ValueError('arg_count must bot be None')

    def decorating_function(func):
        @functools.wraps(func)
        def wrapper(module, calc):
            values = calc.stack.pop(arg_count)

            result = func(*values)

            if push_multiple:
                calc.stack.push(*result)
            else:
                calc.stack.push(result)
        return wrapper

    if func is not None:
        return decorating_function(func)
    else:
        return decorating_function


class Operation:
    """
    An Operation stores multiple methods which all do the same operation
    but require different arguments. There are different supported method
    types: ``'calc'``, ``'plain'`` and ``'remote'``. Additionally it is
    possible to add ``stack`` type methods, however this actually adds a
    ``calc`` method (see ``Operation.add_stack``).

    ``name`` is the operation's name and usually a string.

    ``aliases`` is a list of aliases for this operation.

    ``default`` is the method type used if this operation is called
    (``'plain'`` by default). E.g.::

        op_sqr = Operation('sqr', default='plain')
        op_sqr.add('plain', func=lambda x: x**2)
        op_sqr(2)  # shortcut for op_sqr.get_callable('plain')(2)
        # as default is set to 'plain'


    All methods of this operation can be accessed as attributes, so instead
    of using ``op_sqr.methods['plain']`` one can use ``op_sqr.plain``.

    Every method type requires a different set of parameters.
     * A ``'calc'`` method is required to have two parameters: ``module``
       (the module this method is called from) and ``calc`` (the ``Calculator``
       which loaded ``module``).
       Every operation that is meant to be invoked using the calculator prompt
       is required to have a ``'calc'`` method.
     * A ``'plain'`` method is allowed to have any argument count. These
       methods can be used for simple mathematical functions that can be
       called from any other part of the program.
     * A ``'remote'`` method might require any type of argument, including
       ``module`` and ``calc``. However, these must be the first and second
       arguments.
       These methods are called ''remotely'', which meany that the caller does
       not need to know the module that contains this operation, but just
       needs a reference to a Calculator object. As any count of arguments is
       allowed, this method type is essentially a ``'plain'`` method with
       ``module`` and ``calc`` passed to it automatically.


    Example of plain and calc methods::

        class MyModule(Module):

            # Create a new Operation.
            add = Operation('add', aliases=['+'])

            # Add a plain method that handles the gerneral case to
            # add two numbers.
            @add.add('plain')
            def add(x, y):
                return x + y

            # Add a calc method to be able to use it from the calculator
            # prompt.
            @add.add('calc')
            def add(self, calc):  # defined in a Module: self == module
                x, y = calc.stack.pop(2)
                sum = self.add(x, y)  # plain method of self.add is called
                calc.stack.push(sum)

    The calc method is required as all operation from the calculator prompt
    are called by ``calc.do_operation(operation_name)`` which does not allow
    any parameters to be passed.


    As many mathematical operations only require some numbers from stack, a
    ``'stack'`` method can be added, which automatically generates a
    ``'calc'`` method which pops numbers from the stack and pushes the result
    onto it. So instead of the above, one can write::

        class MyModule(Module):

            add = Operation('add', aliases=['+'])

            @add.add('stack', add_plain=True, arg_count=2)
            def add(x, y):
                return x + y

    This removes all the boilerplate code of the ``'calc'`` method. Internally
    this uses ``stack_op`` to generate the ``'calc'`` method. A ``'plain'``
    method can be added as well if True is passed to ``add_plain`` parameter.

    Such mathematical functions usually do not need to have a ``'remote'``
    method as the ``'plain'`` method already does not require to pass Module or
    Calculator objects. So effectively the ``'plain'`` methos also acts as a
    ``'remote'`` method.


    Some operations require the calculator object as its state is changed by
    them. E.g. an operation that stores a number from the stack to a variable
    storage.::

        class MyModule(Module):

            store = Operation('store', aliases=['sto'])

            # Add a simple generic 'store' method.
            @store.add('plain')
            def store(calc, name, value):
                calc.storage[name] = value

            @store.add('calc')
            def store(self, calc):
                name = calc.input_stream.pop()
                value = calc.stack.pop()

                self.sto(calc, name, value)
                # This actually calls the Operation 'store' which calls its
                # 'plain' method by default. Have in mind, that 'store' is NOT
                # actually a method of this Module but references the Operation
                # defined above. So calling 'self.store' does not pass 'self'
                # as first parameter as expected from instance methods.
                # So the above line is equivalent to:
                #  self.sto.plain(calc, name, value)

            # Add a 'remote' method that can be called remotely.
            store.add('remote', from_type='plain', pass_calc=True,
                      pass_module=False)
            # This constructs a 'remote' method from the 'plain' method above.
            # 'pass_calc' and 'pass_module' indicate that a Calculator should
            # be passed but no Module.

    The remote method can be called by::

        remote_store = calc.get_callable('store', type='remote')
        # 'remote' is actually the default type

        remote_store('a', 1)  # store 1 at variable 'a'

    Instead of calling it e.g. by the defined plain method, which requires to
    know which module defined the 'store' operation::

        module.store.plain(calc, 'a', 1)

    """

    def __init__(self, name, aliases=None, doc=None, default='plain'):
        self.name = name
        self.aliases = aliases
        self.doc = doc
        self.default = default
        self.methods = {}

    def __call__(self, *args, **kwargs):
        """Call default method type (specified by ``self.default``)."""
        if self.default in self.methods:
            func = self.get_callable(self.default)
            return func(*args, **kwargs)
        else:
            raise TypeError('Operation {!r} is not callable'.format(self.name))

    def __getattr__(self, name):
        if name in self.methods:
            return self.methods[name]
        return super().__getattribute__(name)

    def has_name(self, name):
        """
        Returns whether this operation is named ``name`` or has an alias
        ``name``.
        """
        return self.name == name or (
            self.aliases is not None and name in self.aliases)

    def get_callable(self, type, calc=None, module=None):
        """
        Returns a callable for the requested method ``type``. ``calc`` and
        ``module`` are only needed if a ``'remote'`` method is requested.
        """
        try:
            func = self.methods[type]
        except KeyError as err:
            # TODO: Better exception
            raise Exception('unsupported type {!r} for Operation {!r}'.format(
                type, self.name))

        if type in ('plain', 'calc'):
            return func
        elif type == 'remote':
            wrapper = func
            return wrapper(module, calc)

    def add_calc(self, func=None, add_plain=False):
        """
        Add a ``'calc'`` method. Such method is required to have the following
        signature::

            def calc_op(module: Module, calc: Calculator) -> None:
                pass  # do anything

        and is expected to return nothing, however this doesn't cause any
        errors. Every operation that might be called from the calculator prompt
        is required to have a ``'calc'`` method.

        If ``func`` is None, a decorator is returned, so a call to this method
        can be used to decorate a function. If ``func`` is given, this
        operation is returned.

        If ``add_plain`` is True, ``Operation.add_plain`` is called on this
        operation to also add the passed function as a ``'plain'`` method.
        """
        def decorating_function(func):
            self.methods['calc'] = func

            if add_plain:
                self.add_plain(func)

            return self

        if func is not None:
            return decorating_function(func)
        else:
            return decorating_function

    def add_plain(self, func=None):
        """
        Add a ``'plain'`` method. Any number of arguments is allowed.

        If ``func`` is None, a decorator is returned.
        """

        def decorating_function(func):
            self.methods['plain'] = func
            return self

        if func is not None:
            return decorating_function(func)
        else:
            return decorating_function

    def add_remote(self, func=None, from_type='plain', pass_module=True,
                   pass_calc=True):
        """
        Add a ``'remote'`` method. If ``func`` is not None, it is used to
        construct the remote method, otherwise a method with type
        ``from_type`` is used. This method type does not need to be available
        when calling this method but must be available when the remote method
        is called.

        ``pass_module`` and ``pass_calc`` define whether ``module`` or ``calc``
        are passed on calling the remote function. ``module`` is used as the
        first parameter, then ``calc``.

        A remote method can be called with any number of parameters.

        Internally a function is stored in ``self.methods['remote']`` that
        requires ``module`` and ``calc`` to be passed. It stores both in its
        local namespace and returns a function that wraps the passed function
        ``func``. When this wrapper is called, it invokes ``func`` with
        parameters ``module``, ``calc`` and any arguments the wrapper was
        called with. (Whether ``module`` and ``calc`` are passed depends on
        ``pass_module`` and ``pass_calc``.)
        """
        if from_type == 'remote':
            raise ValueError('from_type="remote" is not allowed')

        def context_storing_func(module, calc):
            if func is None:
                base_func = self.methods.get(from_type, None)
                if base_func is None:
                    raise Exception()  # TODO

            @functools.wraps(base_func)
            def wrapping_func(*args, **kwargs):
                """
                This wrapper is used to delay execution of ``base_func`` and
                call it with requested parameters ``module`` and ``calc``.
                """
                if pass_module and pass_calc:
                    return base_func(module, calc, *args, **kwargs)
                elif pass_module:
                    return base_func(module, *args, **kwargs)
                elif pass_calc:
                    return base_func(calc, *args, **kwargs)
                else:
                    return base_func(*args, **kwargs)

            return wrapping_func

        self.methods['remote'] = context_storing_func
        return self

    def add_stack(self, func=None, add_plain=False, **kwargs):
        """
        Add a 'calc' method from a method that only requires parameters from
        stack. Internally ``stack_op`` is used to create a 'calc' method. Any
        keyword arguments passed are passed to this method.

        This means this method is basically equivalent to::

            self.add_calc(stack_op(func, **kwargs))


        If ``func`` is None, a decorator is returned.

        If ``add_plain`` is True, a ``'plain'`` method is added as well.
        """
        def decorating_function(func):
            if add_plain:
                self.add_plain(func)
            self.add_calc(stack_op(func, **kwargs))
            return self

        if func is not None:
            return decorating_function(func)
        else:
            return decorating_function

    ADD_HANDLERS = {
        'calc': add_calc,
        'plain': add_plain,
        'stack': add_stack,
        'remote': add_remote,
    }

    def add(self, type, func=None, **kwargs):
        """
        Add a method with specified ``type`` to this operation. Calls one of
        the ``add_TYPE`` methods defined above, all keyword arguments are
        passed to these.

        If ``func`` is None, a decorator is returned.

        Returns this operation.
        """
        def decorating_function(func):
            handler = self.ADD_HANDLERS.get(type, None)
            if handler is not None:
                return handler(self, func, **kwargs)
            else:
                raise Exception('unknown method type {!r}'.format(type))
            return self

        # If a function was passed, do not return a decorator.
        # However, if type is 'remote', func is defined by 'from_type'
        # keyword argument, and func is not used, so it is allowed
        # to be None.
        if func is not None or type == 'remote':
            return decorating_function(func)
        else:
            return decorating_function

    def __repr__(self):
        return ('<Operation: name={!r}, aliases={!r}, methods={!r}>').format(
            self.name, self.aliases, list(self.methods.keys()))


def operation(name, func=None, aliases=None, doc=None, type='plain', **kwargs):
    """
    Returns a new Operation with specified name and aliases. ``func`` is added
    to this operation using the given ``type``. And other keyword arguments
    are passed to ``Operation.add``. If ``func`` is None, a decorator is
    returned.

    ``doc`` is stored in ``operation.doc`` if not None, otherwise the
    function's docstring is used as documentation for the operation.

    An operation 'add' can be created using this function as decorator::

        @operation('add', aliases=['+'], type='plain', ...)
        def add(x, y):
            '''Add two numbers.'''
            return x + y

    In which case ``add`` is an instance of Operator. However, an Operation
    can also be created separately, so the above is equivalent to::

        add = Operation('add', aliases=['+'], doc='Add two numbers.')

        @add.add('plain', ...)
        def add(x, y):
            return x + y
    """

    def decorating_func(func):
        documentation = doc or func.__doc__
        operation = Operation(name, aliases=aliases, doc=documentation)
        return operation.add(type, func, **kwargs)

    if func is not None:
        return decorating_func(func)
    else:
        return decorating_func


class ModuleMeta(type):
    """
    Metaclass for modules. Searches the classes namespace for Operations and
    places a dict of attribute_name: operation into class._operations.
    """

    def __new__(cls, name, bases, namespace, **kwargs):
        result = type.__new__(cls, name, bases, namespace)

        operations = {}

        for base in bases:
            if hasattr(base, '_operations'):
                operations.update(base._operations)

        for attr in namespace:
            if isinstance(namespace[attr], Operation):
                operations[attr] = namespace[attr]
        result._operations = operations

        return result


class Module(metaclass=ModuleMeta):

    def __init__(self, name):
        self.name = name
        self.calc = None

    def load_module(self, calc):
        if self.calc is not None and self.calc is not calc:
            raise ValueError('Module is already loaded by another calculator!')
        self.calc = calc

    def unload_module(self):
        self.calc = None

    def _get_operation(self, name):
        for operation in self._operations.values():
            if operation.has_name(name):
                return operation
        raise NoSuchOperation('operation {!r} not found'.format(name))

    def get_callable(self, name, type='remote'):
        operation = self._get_operation(name)

        func = operation.get_callable(type, module=self, calc=self.calc)
        return func

    def do_operation(self, name):
        func = self.get_callable(name, type='calc')
        func(self, self.calc)

    def is_executable(self, operation):
        """Returns whether the passed operation is executable by
        this module."""
        try:
            self._get_operation(operation)
        except NoSuchOperation:
            return False
        else:
            return True


class Stack:

    def __init__(self, stack=None):
        self.stack = deque(stack or [])

        self.lastx = None

    def pop(self, count=None):
        """Return the last entry pushed onto the stack. If ``count``
        is an int, a list of the last ``count`` entries is returned,
        where the first item is the topmost entry on the stack."""
        if count is None:
            self.lastx = self.stack.pop()
            return self.lastx
        elif isinstance(count, int):
            self.lastx = self.stack[-1]
            return [self.stack.pop() for _ in range(count)]
        else:
            raise ValueError('int or None required')

    def peek(self):
        """
        Return the topmost value from stack without removing it.

        Raises an IndexError if there are no items on stack.
        """
        return self.stack[-1]

    def push(self, *values):
        """Push ``values`` to the stack. The last item of ``values``
        will be put on top of the stack."""
        for value in values:
            self.stack.append(value)

    def clear(self):
        self.stack.clear()

    def rotate(self, n):
        self.stack.rotate(n)

    def __len__(self):
        return len(self.stack)

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

    def load_module_by_name(self, module_name):
        # try to load "littlecalc.modules.MODULE_NAME" first
        full_name = 'littlecalc.modules.{}'.format(module_name)
        spec = importlib.util.find_spec(full_name)

        if spec is None:
            # try to load module with given name directly
            spec = importlib.util.find_spec(module_name)

        if spec is None:
            raise CalculatorError(
                'module {!r} cannot be found'.format(module_name))

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as err:
            raise ModuleLoadError(
                'error loading module {!r}'.format(module_name)) from err

        calc_modules = module.get_modules(self)
        # TODO: for now load all modules
        for calc_module in calc_modules:
            self.load_module(calc_module)

    def load_module(self, module):
        module.load_module(self)
        self.modules.append(module)

    def unload_module_by_name(self, module_name):
        module_to_unload = None
        for module in self.modules:
            if module_name == module.name:
                module_to_unload = module
                break

        if module_name is None:
            raise CalculatorError('no such module {!r}'.format(module_name))

        self.unload_module(module_to_unload)

    def unload_module(self, module):
        module.unload_module()
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

    def get_module(self, module_name):
        """Return module with given name, return None if no such
        module could be found."""
        for module in self.modules:
            if module.name == module_name:
                return module
        return None

    def find_module_of_operation(self, operation):
        for module in self.modules:
            if module.is_executable(operation):
                return module
        raise NoSuchOperation(operation)

    def do_operation(self, name):
        """Invokes the desired operation."""
        module = self.find_module_of_operation(name)
        module.do_operation(name)

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
