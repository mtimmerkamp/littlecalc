littlecalc
==========

`littlecalc` is a small expandable rpn calculator written in Python. It can be 
extended via "modules" which can add new operations and numeric types.

The project name is not fixed yet, it might be changed as there is already a 
ton of software called "littlecalc". (Who would have thought it?)

This calculator is meant to be a simple (not too complex) calculator like a 
scientific pocket calculator with some advanced features like a history, 
builtin constants and evaluating simple functions. It might even become 
programmable to some extend (that means not using modules but using the 
calculator prompt). However it is not meant to be a graphic calculator or 
CAS (computer algebra system).


Modules
-------

Currently there are two builtin modules:
 * `decimal`: This module uses Python's decimal module to implement common 
   operations on real numbers with arbitrary precision.
 * `constants`: This module supplies important mathematical and physical
   constants.
