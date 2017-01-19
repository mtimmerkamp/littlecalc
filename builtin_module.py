from littlecalc import Module


builtin_module = Module('builtin')


# basic mathematical operations

@builtin_module.register('add')
def add(calc):
    x, y = calc.stack.pop(2)
    calc.stack.push(y + x)


@builtin_module.register('sub')
def sub(calc):
    x, y = calc.stack.pop(2)
    calc.stack.push(y - x)


@builtin_module.register('mul')
def mul(calc):
    x, y = calc.stack.pop(2)
    calc.stack.push(y * x)


@builtin_module.register('div')
def div(calc):
    x, y = calc.stack.pop(2)
    calc.stack.push(y / x)


builtin_module.add_alias('+', 'add')
builtin_module.add_alias('-', 'sub')
builtin_module.add_alias('*', 'mul')
builtin_module.add_alias('/', 'div')
