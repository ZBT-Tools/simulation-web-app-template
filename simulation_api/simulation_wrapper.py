from simulation_api import sofc_cantera_ood as sofc
import cantera as ct


def run_external_simulation(settings):
    """
    Function to call external simulation. Right now a sample calculation is
    conducted to exemplify format of inputs and results.
    """

    # global_results = \
    #     [{'Stack Voltage': {'value': 4.09, 'units': 'V'},
    #       'Average Cell Voltage': {'value': 0.409, 'units': 'V'},
    #       'Average Current Density': {'value': 20007.58, 'units': 'A/m²'},
    #       'Stack Power Density': {'value': 81827.70, 'units': 'W/m²'},
    #       'Stack Power': {'value': 4091.39, 'units': 'W'}}]
    # local_data = \
    #     [{'Channel Location':
    #         {'value': [0., 0.05, 0.1, 0.15, 0.2],
    #          'units': 'm', 'label': 'Channel Location'},
    #       'Cells': {'value': [[0, 1, 2]], 'units': '-'},
    #       'Current Density':
    #         {'value': [[24291.64, 23666.69, 23223.75, 22438.95, 21353.68],
    #                    [24532.59, 23422.90, 23175.77, 22490.50, 21413.87],
    #                    [24634.67, 23344.17, 23145.89, 22505.89, 21440.97]],
    #          'units': 'A/m²', 'xkey': 'Channel Location'}}]
    # additional_data = None


    sofc_settings = {
        "anode": {
            "TPB_length_per_area": 1.0e7,
            "surf_name": 'anode surface',
            "oxide_surf_name": 'anode-side oxide surface'},
        "cathode": {
            "TPB_length_per_area": 1.0e7,
            "surf_name": 'cathode surface',
            "oxide_surf_name": 'cathode-side oxide surface'},
        "T": 1073.15,
        "P": 101325.0,
        "anode_gas_X": 'H2:0.97, H2O:0.03',
        "cathode_gas_X": 'O2:1.0, H2O:0.001',
        "tss": 50.0,
        "sigma": 2.0,
        "ethick": 5.0e-5}

    sofc_parameters = sofc.SOFCParameters(
        anode_parameters=sofc.ElectrodeParameters(
            TPB_length_per_area=
            sofc_settings['anode']['TPB_length_per_area'],
            surf_name=
            sofc_settings['anode']['surf_name'],
            oxide_surf_name=
            sofc_settings['anode']['oxide_surf_name'],
        ),
        cathode_parameters=sofc.ElectrodeParameters(
            TPB_length_per_area=
            sofc_settings['cathode']['TPB_length_per_area'],
            surf_name=
            sofc_settings['cathode']['surf_name'],
            oxide_surf_name=
            sofc_settings['cathode']['oxide_surf_name'],
        ),
        T=sofc_settings['T'],
        P=sofc_settings['P'],
        anode_gas_X=sofc_settings['anode_gas_X'],
        cathode_gas_X=sofc_settings['cathode_gas_X'],
        tss=sofc_settings['tss'],
        sigma=sofc_settings['sigma'],
        ethick=sofc_settings['ethick']
    )
    # Create Simulation Model
    sofc_model = sofc.CanteraSOFC(sofc_parameters)
    # Simulate
    sofc_model.potential_variation()

    return None
    # return global_results, local_data, additional_data


if __name__ == "__main__":

    run_external_simulation(None)