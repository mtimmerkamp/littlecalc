# littlecalc

`littlecalc` is a small expandable rpn calculator written in Python. It can be extended via "modules" which can add new operations and numeric types.

The project name is not fixed yet, so it might be changed as there is already a ton of software called "littlecalc". (Well, who would have thought?)

This calculator is meant to be a "simple" scientific calculator like a pocket calculator with some advanced features like a history, builtin constants and evaluating simple functions. There are also ideas to implement some support for physical units in conjunction with the `constants` module.
It might even become programmable to some extend (that means not using modules but the calculator prompt). However it is not meant to be a graphic calculator or CAS (computer algebra system).

## Modules

Currently there are three builtin modules:

 * `builtins`: Contains several general operations useful for rpn calculators.
 * `decimal`: This module uses Python's decimal module to implement common operations on real numbers with arbitrary precision.
 * `constants`: This module supplies some important mathematical and physical constants.

All of these are currently loaded by default when starting the program.


## Planned features

 * History and simple editing at the prompt.
  * Save history to file?
 * Support for evaluating formulas (probably only if notated in rpn).
 * User and developer documentation...

 * For module `decimal`:
  * Validate implemented mathematical algorithms to be correct.


## Quickstart

Python >= 3.5 is required.

To run interactive prompt from source:

```
python -m littlecalc.tui
```


To install, just run:

```
python setup.py install
```

Then you can start via `littlecalc`.
