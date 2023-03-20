[
  {
    "title": "Cells",
    "show_title": false,
    "sub_frame_dicts": [
      {
        "title": "Cell Settings",
        "show_title": false,
        "font": "Arial 10 bold",
        "sticky": "WEN",
        "sub_frame_dicts": [
          {
            "title": "Cell Lengths",
            "show_title": true,
            "font": "Arial 10 bold",
            "widget_dicts": [
              {
                "label": "Cell Length:",
                "dimensions": "m",
                "value": 0.1,
                "sim_name": ["cell", "length"],
                "dtype": "float",
                "size_label": "xl",
                "size_unit": "s",
                "type": "EntrySet"
              },
              {
                "label": "Anode",
                "row": 5,
                "column": 1,
                "type": "Label",
                "sticky": "WENS"
              },
              {
                "label": "Cathode",
                "row": 5,
                "column": 2,
                "type": "Label",
                "sticky": "WENS"
              },
              {
                "label": "BPP Thickness:",
                "number": 2,
                "value": 0.002,
                "sim_name": [["anode", "bpp", "thickness"],
                             ["cathode","bpp","thickness"]],
                "dtype": "float",
                "dimensions": "m",
                "type": "EntrySet"
              }
            ],
            "size_label": "l",
            "size_unit": "s",
            "sticky": "WESN"
          },
          {
            "title": "Flow Field Settings",
            "show_title": true,
            "font": "Arial 10 bold",
            "widget_dicts": [
              {
                "label": "Anode",
                "row": 1,
                "column": 1,
                "type": "Label",
                "sticky": "WENS"
              },
              {
                "label": "Cathode",
                "row": 1,
                "column": 2,
                "type": "Label",
                "sticky": "WENS"
              },
              {
                "label": "Shape of Cross-Section:",
                "number": 2,
                "sim_name": [["anode", "channel", "cross_sectional_shape"],
                             ["cathode", "channel", "cross_sectional_shape"]],
                "value": ["rectangular", "trapezoidal", "triangular"],
                "specifier": "dropdown_activate_basewidth",
                "type": "ComboboxSet",
                "sticky": "WN"
              },
              {
                "label": "Channel Width:",
                "number": 2,
                "value": [0.001, 0.001],
                "sim_name": [["anode", "channel", "width"],
                             ["cathode", "channel", "width"]],
                "dtype": "float",
                "dimensions": "m",
                "type": "EntrySet",
                "sticky": ["NW", "NWE"]
              },
              {
                "label": "Rib Width:",
                "number": 2,
                "value": [0.001, 0.001],
                "sim_name": [["anode", "channel", "rib_width" ],
                             ["cathode", "channel", "rib_width"]],
                "dtype": "float",
                "dimensions": "m",
                "type": "EntrySet",
                "sticky": ["NW", "NWE"]
              },
              {
                "label": "Base Width:",
                "number": 2,
                "value": [0.001, 0.001],
                "sim_name": [["anode", "channel", "base_width"],
                             ["cathode", "channel", "base_width"]],
                "dtype": "float",
                "dimensions": "m",
                "type": "EntrySet",
                "specifier": "disable_basewidth",
                "sticky": ["NW", "NWE"]
              }
            ],
            "size_label": "l",
            "size_unit": "s",
            "sticky": "WENS"
          }
        ]
      }
    ]
  },
  {
    "title": "Physical Properties",
    "show_title": false,
    "sub_frame_dicts": [
      {
        "title": "Physical Properties",
        "show_title": false,
        "font": "Arial 10 bold",
        "sticky": "WEN",
        "sub_frame_dicts": [
          {
            "title": "Porous Layers",
            "show_title": true,
            "font": "Arial 10 bold",
            "sticky": "WEN",
            "size_label": "s",
            "size_unit": "l",
            "widget_dicts": [
              {
                "label": "Anode",
                "row": 1,
                "column": 1,
                "pady": 0,
                "type": "Label",
                "sticky": "WENS"
              },
              {
                "label": "Cathode",
                "row": 1,
                "column": 3,
                "pady": 0,
                "type": "Label",
                "sticky": "WENS"
              },
              {
                "label": "ip",
                "row": 2,
                "column": 1,
                "pady": 0,
                "type": "Label",
                "sticky": "WENS"
              },
              {
                "label": "tp",
                "row": 2,
                "column": 2,
                "pady": 0,
                "type": "Label",
                "sticky": "WENS"
              },
              {
                "label": "ip",
                "row": 2,
                "column": 3,
                "pady": 0,
                "type": "Label",
                "sticky": "WENS"
              },
              {
                "label": "tp",
                "row": 2,
                "column": 4,
                "pady": 0,
                "type": "Label",
                "sticky": "WENS"
              },
              {
                "label": "BPP Electrical Conductivity:",
                "number": 4,
                "value": 60000.0,
                "width": 5,
                "sim_name": [
                  ["anode", "bpp", "electrical_conductivity", [0, 1]],
                  ["cathode", "bpp", "electrical_conductivity", [2, 3]]],
                "dtype": "float",
                "dimensions": "S/m",
                "type": "EntrySet"
              }
            ]
          },
          {
            "title": "Membrane Settings",
            "show_title": true,
            "font": "Arial 10 bold",
            "sticky": "WEN",
            "sub_frame_dicts": [
              {
                "title": "Membrane Model Settings",
                "show_title": false,
                "font": "Arial 10 bold",
                "sticky": "WEN",
                "size_label": "l",
                "size_unit": "l",
                "widget_dicts": [
                  {
                    "label": "Membrane Model:",
                    "number": 1,
                    "sim_name": [
                      "membrane",
                      "type"
                    ],
                    "value": ["Constant", "Springer", "Linear"],
                    "type": "ComboboxSet",
                    "specifier": "dropdown_activate"
                  },
                  {
                    "title": "Constant Ionic Conductivity",
                    "specifier": "visibility",
                    "widget_dicts": [
                      {
                        "label": "Ionic Conductivity:",
                        "value": 5.0,
                        "sim_name": ["membrane", "ionic_conductivity"],
                        "dtype": "float",
                        "dimensions": "S/m",
                        "type": "EntrySet"
                      },
                      {
                        "label": " ",
                        "type": "Label",
                        "sticky": "WENS"
                      }
                    ],
                    "sticky": "WEN"
                  },
                  {
                    "title": "Springer Ionic Conductivity",
                    "specifier": "visibility",
                    "widget_dicts": [
                      {
                        "label": " ",
                        "type": "Label",
                        "sticky": "WENS"
                      },
                      {
                        "label": " ",
                        "type": "Label",
                        "sticky": "WENS"
                      }
                    ],
                    "sticky": "WEN"
                  },
                  {
                    "title": "Linear Ionic Conductivity",
                    "specifier": "visibility",
                    "widget_dicts": [
                      {
                        "label": "Constant Resistance Coefficient:",
                        "value": 4.3e-05,
                        "sim_name": ["membrane", "basic_resistance"],
                        "dtype": "float",
                        "dimensions": "Ohm-m\u00b2",
                        "type": "EntrySet"
                      },
                      {
                        "label": "Linear Temperature Coefficient:",
                        "value": 7e-08,
                        "sim_name": ["membrane", "temperature_coefficient"],
                        "dtype": "float",
                        "dimensions": "Ohm-m\u00b2/K",
                        "type": "EntrySet"
                      }
                    ],
                    "sticky": "WEN"
                  }
                ]
              }
            ]
          }
        ]
      }
    ]
  }
]