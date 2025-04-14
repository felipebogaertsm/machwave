from dataclasses import dataclass, field
from rocketcea.cea_obj import CEA_Obj
import scipy.constants


# Example conversion function (already provided in your codebase).
def convert_pa_to_psi(pressure_pa: float) -> float:
    return pressure_pa * 0.00014503773773  # 1 Pa = 0.0001450377 psi


@dataclass
class BiliquidPropellant:
    """
    Class that stores liquid propellant data and interfaces with RocketCEA.

    Attributes:
        oxidizer_name: RocketCEA-compatible oxidizer name.
        fuel_name: RocketCEA-compatible fuel name.
        of_ratio: Oxidizer-to-fuel ratio (dimensionless).
        density: Reference density of the (combined) propellant or any desired reference [kg/m^3].
        combustion_efficiency: Overall combustion efficiency (0 to 1).
        T0_ideal: Ideal combustion temperature [K].
        k_mix: Isentropic exponent for the combustion chamber region.
        k_ex: Isentropic exponent for the exhaust region.
        M_ch: Approximate molar weight in the chamber [kg/mol].
        M_ex: Approximate molar weight in the exhaust [kg/mol].
        Isp_frozen: A reference or typical frozen-flow Isp [s].
        Isp_shifting: A reference or typical shifting-flow Isp [s].
    """

    oxidizer_name: str
    fuel_name: str
    of_ratio: float

    # Optional additional fields you might want on the propellant
    density: float = 1000.0
    combustion_efficiency: float = 0.98
    T0_ideal: float = 3500.0
    k_mix: float = 1.2
    k_ex: float = 1.2
    M_ch: float = 0.028  # e.g. 28 g/mol = 0.028 kg/mol
    M_ex: float = 0.028
    Isp_frozen: float = 250.0
    Isp_shifting: float = 270.0

    # Fields for storing updated RocketCEA results (populated later)
    combustion_temperature: float
    chamber_pressure: float
    chamber_gamma: float
    exit_gamma: float
    chamber_molecular_weight: float
    exit_molecular_weight: float
    chamber_density: float

    def __post_init__(self):
        # Instantiate the RocketCEA object for the given oxidizer and fuel.
        self.cea_obj = CEA_Obj(oxName=self.oxidizer_name, fuelName=self.fuel_name)

        # Demonstration of how you might adjust T0 for efficiency:
        self.T0 = self.T0_ideal * self.combustion_efficiency

        # Gas constants based on approximate M_ch and M_ex
        self.R_ch = scipy.constants.R / self.M_ch
        self.R_ex = scipy.constants.R / self.M_ex

    def update_properties(
        self, chamber_pressure: float, eps: float = 1.0, frozen: int = 0
    ) -> None:
        """
        Update propellant properties using RocketCEA for a given chamber_pressure.

        Args:
            chamber_pressure: Chamber pressure in Pa.
            eps: Nozzle area expansion ratio (Ae/At).
            frozen: If True, compute frozen-flow properties; otherwise shifting-flow.
        """
        # 1) Convert from Pa to psi
        chamber_pressure_psi = convert_pa_to_psi(chamber_pressure)

        # 2) Get the combustion temperature
        self.combustion_temperature = self.cea_obj.get_Tcomb(
            Pc=chamber_pressure_psi, MR=self.of_ratio
        )

        # 3) Get densities
        self.chamber_density = self.cea_obj.get_Densities(
            Pc=chamber_pressure_psi, MR=self.of_ratio, eps=eps, frozen=frozen
        )[
            0
        ]  # 1st index is the chamber density

        # 4) Get chamber mol. weight and gamma
        ch_molwt_g, ch_gamma = self.cea_obj.get_Chamber_MolWt_gamma(
            Pc=chamber_pressure_psi, MR=self.of_ratio, eps=eps
        )
        # Convert from g/mol to kg/mol
        self.chamber_molecular_weight = ch_molwt_g / 1000.0
        self.chamber_gamma = ch_gamma

        # 5) Get exit mol. weight and gamma
        ex_molwt_g, ex_gamma = self.cea_obj.get_exit_MolWt_gamma(
            Pc=chamber_pressure_psi, MR=self.of_ratio, eps=eps, frozen=frozen
        )
        self.exit_molecular_weight = ex_molwt_g / 1000.0
        self.exit_gamma = ex_gamma
