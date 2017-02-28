#! /usr/bin/env python3
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

import traceback
import readline

from littlecalc.core import Calculator, CalculatorError


class TUICalculator(Calculator):

    def __init__(self):
        super().__init__()

    def output(self, text):
        print(text)


def main():
    calc = TUICalculator()

    calc.load_module_by_name('builtins')
    calc.load_module_by_name('decimal')
    calc.load_module_by_name('constants')

    while True:
        try:
            user_input = input('>>> ')
        except KeyboardInterrupt:
            print()  # print new line before exiting
            break

        try:
            calc.parse_input(user_input)
        except CalculatorError:
            print('An error occurred:')
            traceback.print_exc()

        max_depth = min(len(calc.stack.stack), 4)
        if max_depth > 0:
            for i, level_name in enumerate('TZYX'[-max_depth:]):
                value = calc.stack.stack[-max_depth + i]
                print('{}: {}'.format(level_name, value))


if __name__ == '__main__':
    main()
