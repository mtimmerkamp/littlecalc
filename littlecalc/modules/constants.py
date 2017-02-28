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

from decimal import localcontext
import traceback
from littlecalc.core import Module, CalculatorError, operation


class ConstantError(CalculatorError):
    pass


class UnknownConstantError(ConstantError):

    def __init__(self, constant_id):
        super().__init__('No such constant: "{}"'.format(constant_id))


class ConstantCalculationError(ConstantError):
    pass


class ConstantsModule(Module):

    def __init__(self):
        super().__init__('constants')

        self.descriptions = {}
        """Mapping a constant's id to a short description."""

        self.fixed_constants = {}
        """Mapping a constant's id to its value. Only for constants
        which are known to a fixed precision and therefore
        independent of the current calculator precision."""

        self.constant_calculators = {}
        """Mapping a constant's id to a function that can calculate
        the constant up to the current precision of the calculator."""

    def get(self, calculator, constant_id):
        """Returns a numeric value for the requested constant. An
        ``UnknownConstantError`` is raised if an unknown constant
        id is passed. If an error occurs while calculating a
        constant, a ``ConstantCalculationError`` is raised.

        The requested constant will be returned as by
        ``Calculator.to_numeric``.

        If there is a function available to calculate the requested
        constant, it will be used instead of a stored fixed value.
        """
        try:
            func = self.constant_calculators[constant_id]
        except KeyError:
            try:
                value = self.fixed_constants[constant_id]
            except KeyError:
                raise UnknownConstantError(constant_id)
            return calculator.to_numeric(value)

        try:
            return func(calculator, self)
        except Exception as err:
            raise ConstantCalculationError(
                'Cannot calculate constant: "{}"'.format(constant_id)
            ) from err

    def __contains__(self, item):
        return item in self.descriptions

    def __iter__(self):
        return iter(self.descriptions)

    def add(self, constant_id, description, value=None, func=None):
        """Add a constant to constant store. ``constant_id`` and
        ``description`` are required as well as one of ``value``
        and ``func``. ``value`` is a string to be converted
        by ``Calculator.to_numeric``, while ``func`` is a function
        that takes a calculator object and an instance of this
        class as parameters.

        If ``value`` is set, a fixed constant is created.
        If ``func`` is set, the function will be called each time the
        constant is requested to allow calculating the constant to the
        current calculator precision.
        """
        if value is None and func is None:
            raise ValueError('value and func must not both be None')
        elif value is not None and func is not None:
            raise ValueError('value and func must not both be set')

        self.descriptions[constant_id] = description
        if value is not None:
            self.fixed_constants[constant_id] = value
        else:
            self.constant_calculators[constant_id] = func

    @operation('const', type='plain')
    def const(self, calc, constant_id):
        return self.get(calc, constant_id)
    const.add('remote', from_type='plain')

    @const.add('calc')
    def const(self, calc):
        if calc.input_stream.has_next():
            constant_id = calc.input_stream.pop()
        else:
            raise CalculatorError('argument missing: constant id')

        try:
            value = self.const(self, calc, constant_id)
        except ConstantError as err:
            calc.output(traceback.format_exc())
        else:
            calc.stack.push(value)


def calc_e(calc, module):
    to_num = calc.to_numeric
    with localcontext() as ctx:
        ctx.prec += 5
        i, fact, num = 0, 1, to_num('1.0')
        lasts, s = to_num('0'), to_num('1.0')
        while s != lasts:
            lasts = s
            i += 1
            fact *= i
            # num *= 1  # calculation of e^1
            s += num / fact
    return +s  # rounding back to original precision


def calc_pi(calc, module):
    to_num = calc.to_numeric
    with localcontext() as ctx:
        ctx.prec += 5  # increase precision for intermediate steps

        const_0p5 = to_num('0.5')

        # Gauss-Legendre algorithm
        an, bn, tn, pn = to_num(1), 1 / to_num(2)**const_0p5, 1 / to_num(4), 1
        v, lastv = 0, 1
        while v != lastv:
            a, b, t, p = an, bn, tn, pn

            an = (a + b) / 2
            bn = (a * b)**const_0p5
            tn = t - p * (a - an)**2
            pn = 2 * p

            lastv = v
            v = (an + bn)**2 / (4 * tn)

    return +v  # round back to previous precision


def calc_phys_mu0(calc, module):
    pi = module.get(calc, 'pi')
    return 4 * pi * calc.to_numeric('1e-7')


def calc_phys_eps0(calc, module):
    mu0 = module.get(calc, 'mu0')
    c0 = module.get(calc, 'c0')

    return 1 / (mu0 * c0)


def calc_phys_Z0(calc, module):
    mu0 = module.get(calc, 'mu0')
    c0 = module.get(calc, 'c0')

    return c0 * mu0


def add_default_constants(module):
    module.add('e', 'Euler\'s number', func=calc_e)
    module.add('pi', 'ratio of a circle\'s circumference to its diameter',
               func=calc_pi)

    # 2014 CODATA recommended values
    # Fundamental Physical Constants (from http://physics.nist.gov/constants)
    # universal constants
    module.add('c0', 'speed of light in vacuum (m s^-1)', '299792458')
    module.add('mu0', 'magnetic constant (N A^-2)', func=calc_phys_mu0)
    module.add('eps0', 'electric constant (F m^-1)', func=calc_phys_eps0)
    module.add(
        'Z0', 'characteristic impedance of vacuum (Ohm)', func=calc_phys_Z0)
    module.add(
        'G', 'Newtonian constant of gravitation (m^3 kg^-1 s^-2)',
        '6.67408e-11')
    module.add('h', 'Planck constant (J s)', '6.626070040e-34')
    module.add('hbar', 'Planck constant over 2 pi (J s)', '1.054571800e-34')
    module.add('m_P', 'Planck mass (kg)', '2.176470e-8')
    module.add('T_P', 'Planck temperature (K)', '1.416808e32')
    module.add('l_P', 'Planck length (m)', '1.616229e-35')
    module.add('t_P', 'Planck time (s)', '5.39116e-44')

    # electromagnetic constants
    module.add('e0', 'elementary charge (C)', '1.6021766208e-19')
    module.add('Phi0', 'magnetic flux quantum (Wb)', '2.067833831e-15')
    module.add('G0', 'conductance quantum (S)', '7.7480917310e-5')
    module.add('K_J', 'Josephson constant (Hz V^-1)', '483597.8525e9')
    module.add('R_K', 'von Klitzing constant (Ohm)', '25812.8074555')
    module.add('mu_B', 'Bohr magneton (J T^-1)', '927.4009994e-26')
    module.add('mu_N', 'nuclear magneton (J T^-1)', '5.050783699e-27')

    # physio-chemical constants
    module.add('N_A', 'Avogadro constant (mol^-1)', '6.022140857e23')
    module.add('m_u', 'atomic mass constant (kg)', '1.660539040e-27')
    module.add('F', 'Faraday constant (C mol^-1)', '96485.33289')
    module.add('R', 'molar gas constant (J mol^-1 K^-1)', '8.3144598')
    module.add('k_B', 'Boltzmann constant (J K^-1)', '1.38064852e-23')
    module.add(
        'V_m', ('molar volume of ideal gas (m^3 mol^-1) ' +
                '(at 273.15 K, 101.325 kPa)'),
        '22.413962e-3')
    module.add(
        'sigma', 'Stefan-Boltzmann constant (W m^-2 K^-4)', '5.670367e-8')
    module.add('c1', 'first radiation constant (W m^2)', '3.741771790e-16')
    module.add('c2', 'second radiation constant (m K)', '1.43877736e-2')

    # atomic and nuclear constants
    module.add('alpha', 'fine-structure constant', '7.2973525664e-3')
    module.add('Ry', 'Rydberg constant (m^-1)', '10973731.568508')
    module.add('a0', 'Bohr radius (m)', '0.52917721067e-10')
    module.add('E_h', 'Hartree energy (J)', '4.359744650e-18')

    module.add('m_e', 'electron mass (kg)', '9.10938356e-31')
    module.add('lambda_C', 'Compton wavelength (m)', '2.4263102367e-12')
    module.add('r_e', 'classical electron radius (m)', '2.8179403227e-15')
    module.add('mu_e', 'electron magnetic moment (J T^-1)', '-928.4764620e-26')
    module.add('g_e', 'electron g factor', '-2.00231930436182')

    module.add('m_mu', 'muon mass (kg)', '1.883531594e-28')
    module.add('mu_mu', 'muon magnetic moment (J T^-1)', '-4.49044826e-26')
    module.add('g_mu', 'muon g factor', '-2.0023318418')

    module.add('m_tau', 'tau mass (kg)', '3.16747e-27')

    module.add('m_p', 'proton mass (kg)', '1.672621898e-27')
    module.add('mu_p', 'proton magnetic moment (J T^-1)', '1.4106067873e-26 ')
    module.add('g_p', 'proton g factor', '5.585694702')

    module.add('m_n', 'neutron mass (kg)', '1.674927471e-27')
    module.add('mu_n', 'neutron magnetic moment (J T^-1)', '-0.96623650e-26')
    module.add('g_n', 'neutron g factor', '-3.82608545')

    module.add('m_d', 'deuteron mass (kg)', '3.343583719e-27')
    module.add('mu_d', 'deuteron magnetic moment (J T^-1)', '0.4330735040e-26')
    module.add('g_d', 'deuteron g factor', '0.8574382311')

    module.add('m_t', 'triton mass (kg)', '5.007356665e-27')
    module.add('mu_t', 'triton magnetic moment (J T^-1)', '1.504609503e-26')
    module.add('g_t', 'triton g factor', '5.957924920')

    module.add('m_h', 'helion mass (kg)', '5.006412700e-27')
    module.add('mu_h', 'helion magnetic moment (J T^-1)', '-1.074617522e-26')
    module.add('g_h', 'helion g factor', '-4.255250616')

    module.add('m_alpha', 'alpha particle mass (kg)', '6.644657230e-27')

    # adopted values
    module.add('g', 'standard acceleration of gravity (m s^-2)', '9.80665')
    module.add('atm', 'standard atmosphere (Pa)', '101325')


def get_modules(calc):
    module = ConstantsModule()
    add_default_constants(module)
    return [module]
