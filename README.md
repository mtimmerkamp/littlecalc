littlecalc
==========

`littlecalc` is a small expandable rpn calculator written in Python. It can be extended via "modules" which can add new operations and numeric types.

The project name is not fixed yet, so it might be changed as there is already a ton of software called "littlecalc". (Well, who would have thought?)

This calculator is meant to be a "simple" scientific calculator like a pocket calculator with some advanced features like a history, builtin constants and evaluating simple functions. There are also ideas to implement some support for physical units in conjunction with the ``constants`` module.
It might even become programmable to some extend (that means not using modules but using the calculator prompt). However it is not meant to be a graphic calculator or CAS (computer algebra system).

Modules
-------

Currently there are two builtin modules:

 * `decimal`: This module uses Python's decimal module to implement common operations on real numbers with arbitrary precision.
 * `constants`: This module supplies some important mathematical and physical constants.

Both of these are currently loaded by default when starting the program.


Quickstart
----------

Python >= 3.3 is required.

To run from source:

    python -m littlecalc.core


To install, just run:

    python setup.py install

Then you can start via ``littlecalc``.
