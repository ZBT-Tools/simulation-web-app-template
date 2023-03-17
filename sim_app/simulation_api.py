
def run_external_simulation(settings):
    """
    Dummy simulation call to external simulation api returning random data,
    however in a compatible format
    """
    global_results = \
        [{'Stack Voltage': {'value': 4.09, 'units': 'V'},
          'Average Cell Voltage': {'value': 0.409, 'units': 'V'},
          'Average Current Density': {'value': 20007.58, 'units': 'A/m²'},
          'Stack Power Density': {'value': 81827.70, 'units': 'W/m²'},
          'Stack Power': {'value': 4091.39, 'units': 'W'}}]
    local_data = \
        [{'Channel Location':
            {'value': [0., 0.05, 0.1, 0.15, 0.2],
             'units': 'm', 'label': 'Channel Location'},
          'Cells': {'value': [[0, 1, 2]], 'units': '-'},
          'Current Density':
            {'value': [[24291.64, 23666.69, 23223.75, 22438.95, 21353.68],
                       [24532.59, 23422.90, 23175.77, 22490.50, 21413.87],
                       [24634.67, 23344.17, 23145.89, 22505.89, 21440.97]],
             'units': 'A/m²', 'xkey': 'Channel Location'}}]
    additional_data = None
    return global_results, local_data, additional_data
