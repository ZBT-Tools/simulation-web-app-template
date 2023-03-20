{
    simulation: {
        elements: 10
    },
    cell: {
        length: 0.5
    },
    simulation_model: {
        type: "Sinus",
        ionic_conductivity: 15.0,
        basic_resistance: 4.3e-05,
        temperature_coefficient: 7e-08
    },
    cathode: {
        name: "Cathode",
        bpp: {
            thickness:
                    0.002,
            electrical_conductivity: [
                60000.0,
                60000.0
            ]
        },
        "channel": {
            "cross_sectional_shape": "rectangular",
            "rib_width": 0.001,
            "base_width": 0.0008,
            "width": 0.001
        }
    },
    "anode": {
        "name": "Anode",
        "bpp": {
            "thickness":
                    0.002,
            "electrical_conductivity": [
                60000.0,
                60000.0
            ]
        },
        "channel": {
            "name": "Anode Channel",
            "cross_sectional_shape": "rectangular",
            "rib_width": 0.001,
            "base_width": 0.0008,
            "width": 0.001
        }
    }
}
