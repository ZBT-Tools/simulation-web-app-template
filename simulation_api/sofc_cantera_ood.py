"""
This is a model retrieved from the Cantera homepage:
https://www.cantera.org/examples/python/surface_chemistry/sofc.py.html)

It was incorporated into and object-oriented design to provide a better
interface for external calling and using it as a demonstration with our GUI
web app template built with Dash.

Original Description:
A simple model of a solid oxide fuel cell.

Unlike most SOFC models, this model does not use semi-empirical Butler-Volmer
kinetics for the charge transfer reactions, but uses elementary, reversible
reactions obeying mass-action kinetics for all reactions, including charge
transfer. As this script will demonstrate, this approach allows computing the
OCV (it does not need to be separately specified), as well as polarization
curves.

NOTE: The parameters here, and in the input file sofc.yaml, are not to be
relied upon for a real SOFC simulation! They are meant to illustrate only how
to do such a calculation in Cantera. While some of the parameters may be close
to real values, others are simply set arbitrarily to give reasonable-looking
results.

It is recommended that you read input file sofc.yaml before reading or running
this script!

Requires: cantera >= 2.6.0
Keywords: kinetics, electrochemistry, surface chemistry, fuel cell
"""

import cantera as ct
import math
import csv
from dataclasses import dataclass

ct.add_module_directory()


@dataclass
class ElectrodeParameters:
    TPB_length_per_area: float
    surf_name: str
    oxide_surf_name: str


@dataclass
class SOFCParameters:
    anode_parameters: ElectrodeParameters
    cathode_parameters: ElectrodeParameters
    T: float  # T in K
    P: float  # # One atm in Pa
    anode_gas_X: str  # Gas composition on anode side
    cathode_gas_X: str  # Gas composition on cathode side

    # time to integrate coverage eqs. to steady state in
    # 'advance_coverages'. This should be more than enough time.
    tss: float

    sigma: float  # electrolyte conductivity [Siemens / m]
    ethick: float  # electrolyte thickness [m]



class Electrode():
    def __init__(self, params: ElectrodeParameters):

        # import the electrode-side triple phase boundary and adjacent phases
        self.tpb = ct.Interface("sofc.yaml", "tpb")
        self.surf = self.tpb.adjacent["metal_surface"]
        self.oxide_surf = self.tpb.adjacent["oxide_surface"]
        self.bulk = self.tpb.adjacent["metal"]
        self.oxide = self.oxide_surf.adjacent["oxide_bulk"]
        self.gas = self.oxide_surf.adjacent["gas"]
        self.surf.name = params.surf_name
        self.oxide_surf.name = params.oxide_surf_name
        self.TPB_length_per_area = params.TPB_length_per_area
        self.oxide_electric_potential = self.oxide.electric_potential

    def curr(self, E):
        """
        Current to the cathode as a function of cathode
        potential relative to electrolyte
        """

        # due to ohmic losses, the cathode-side electrolyte potential is
        # non-zero. Therefore, we need to add this potential to E to get the
        # cathode potential.
        self.bulk.electric_potential = E + self.oxide_electric_potential

        # get the species net production rates due to the cathode-side TPB
        # reaction mechanism. The production rate array has the values for the
        # neighbor species in the order listed in the .yaml file, followed by the
        # tpb phase. The kinetics_species_index method finds the index of the species,
        # accounting for the possibility of species being in different orders in the
        # arrays.
        w = self.tpb.net_production_rates
        electron_index = self.tpb.kinetics_species_index('electron')

        # the sign convention is that the current is positive when electrons are
        # being drawn from the cathode (that is, negative production rate).
        return -ct.faraday * w[electron_index] * self.TPB_length_per_area


class CanteraSOFC():
    def __init__(self, params: SOFCParameters):
        self.ethick = params.ethick
        self.sigma = params.sigma
        #####################################################################
        # Anode-side phases
        #####################################################################
        # import the anode-side triple phase boundary and adjacent phases
        self.anode = Electrode(params.anode_parameters)

        #####################################################################
        # Cathode-side phases
        #####################################################################
        # Here for simplicity we are using the same phase and interface
        # models for the cathode as we used for the anode. In a more
        # realistic simulation, separate models would be used for the
        # cathode, with a different reaction mechanism.
        self.cathode = Electrode(params.cathode_parameters)

        # the anode-side electrolyte potential is kept at zero. Therefore, the
        # anode potential is just equal to E.
        self.anode.oxide_electric_potential = 0.0

        # Initialization
        # Set the gas compositions, and temperatures of all phases

        self.anode.gas.TPX = params.T, params.P, params.anode_gas_X
        self.anode.gas.equilibrate('TP')  # needed to use equil_OCV

        self.cathode.gas.TPX = params.T, params.P, params.cathode_gas_X
        self.cathode.gas.equilibrate('TP')  # needed to use equil_OCV

        phases = [
            self.anode.bulk, self.anode.surf, self.anode.oxide_surf,
            self.anode.oxide,
            self.cathode.bulk, self.cathode.surf, self.cathode.oxide_surf,
            self.cathode.oxide,
            self.anode.tpb, self.cathode.tpb]
        for p in phases:
            p.TP = params.T, params.P

        # now bring the surface coverages into steady state with these gas
        # compositions. Note that the coverages are held fixed at these values - we do
        # NOT consider the change in coverages due to TPB reactions. For that, a more
        # complex model is required. But as long as the thermal chemistry is fast
        # relative to charge transfer, this should be an OK approximation.
        for s in [self.anode.surf, self.anode.oxide_surf,
                  self.cathode.surf, self.cathode.oxide_surf]:
            s.advance_coverages(params.tss)
            self.show_coverages(s)

        # find open circuit potentials by solving for the E values that give
        # zero current.
        self.Ea0 = self.NewtonSolver(self.anode.curr, xstart=-0.51)
        self.Ec0 = self.NewtonSolver(self.cathode.curr, xstart=0.51)

        print('\nocv from zero current is: ', self.Ec0 - self.Ea0)
        print('OCV from thermo equil is: ',
              self.equil_OCV(self.anode.gas, self.cathode.gas))

        print('Ea0 = ', self.Ea0)
        print('Ec0 = ', self.Ec0)
        print()

        # do polarization curve for anode overpotentials from -250 mV
        # (cathodic) to +250 mV (anodic)
        self.Ea_min = self.Ea0 - 0.25
        self.Ea_max = self.Ea0 + 0.25

        self.output_data = []

    def show_coverages(self, surface):
        """Print the coverages for surface s."""
        print('\n{0}\n'.format(surface.name))
        cov = surface.coverages
        names = surface.species_names
        for n in range(surface.n_species):
            print('{0:16s}  {1:13.4g}'.format(names[n], cov[n]))

    def equil_OCV(self, gas1, gas2):
        return (-ct.gas_constant * gas1.T *
                math.log(gas1['O2'].X / gas2['O2'].X) / (4.0*ct.faraday))

    # this function is defined to use with NewtonSolver to invert the current-
    # voltage function. NewtonSolver requires a function of one variable, so the
    # other objects are accessed through the global namespace.
    def NewtonSolver(self, f, xstart, C=0.0):
        """
        Solve f(x) = C by Newton iteration.
        - xstart    starting point for Newton iteration
        - C         constant
        """
        f0 = f(xstart) - C
        x0 = xstart
        dx = 1.0e-6
        n = 0
        while n < 200:
            ff = f(x0 + dx) - C
            dfdx = (ff - f0)/dx
            step = - f0/dfdx

            # avoid taking steps too large
            if abs(step) > 0.1:
                step = 0.1*step/abs(step)

            x0 += step
            emax = 0.00001  # 0.01 mV tolerance
            if abs(f0) < emax and n > 8:
                return x0
            f0 = f(x0) - C
            n += 1
        raise Exception('no root!')

    def potential_variation(self):

        # vary the anode overpotential, from cathodic to anodic polarization
        for n in range(100):
            Ea = self.Ea_min + 0.005*n

            # set the electrode potential. Note that the anode-side electrolyte is
            # held fixed at 0 V.
            self.anode.bulk.electric_potential = Ea

            # compute the anode current
            curr = self.anode.curr(Ea)

            # set potential of the oxide on the cathode side to reflect the
            # ohmic drop through the electrolyte
            delta_V = curr * self.ethick / self.sigma

            # if the current is positive, negatively-charged ions are flowing
            # from the cathode to the anode. Therefore, the cathode side must
            # be more negative
            # than the anode side.
            phi_oxide_c = -delta_V

            # note that both the bulk and the surface potentials must be set
            self.cathode.oxide.electric_potential = phi_oxide_c
            self.cathode.oxide_surf.electric_potential = phi_oxide_c

            # Find the value of the cathode potential relative to the
            # cathode-side electrolyte that yields the same current density
            # as the anode current
            # density
            Ec = self.NewtonSolver(self.cathode.curr,
                                   xstart=self.Ec0+0.1, C=curr)

            self.cathode.bulk.electric_potential = phi_oxide_c + Ec

            # write the current density, anode and cathode overpotentials, ohmic
            # overpotential, and load potential
            self.output_data.append(
                [0.1*curr, Ea - self.Ea0, Ec - self.Ec0, delta_V,
                                self.cathode.bulk.electric_potential -
                                self.anode.bulk.electric_potential])

    def write_output(self):
        with open("sofc.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['i (mA/cm2)', 'eta_a', 'eta_c', 'eta_ohmic', 'Eload'])
            writer.writerows(self.output_data)
        print('polarization curve data written to file sofc.csv')
