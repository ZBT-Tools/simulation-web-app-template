import base64
import io
import itertools
import os
from dash import dash_table
import numpy as np
import pandas as pd
import pickle
import copy
import sys
import json
import dash
from dash_extensions.enrich import Output, Input, State, ALL, html, dcc, \
    ServersideOutput, ctx
from dash import dash_table as dt
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from plotly.subplots import make_subplots
# import plotly.express as px

from sim_app.dash_functions import create_settings
from . import dash_functions as df, dash_layout as dl, dash_modal as dm
from . import dash_layout_new as dl_new
# import dash_functions as df, dash_layout as dl, dash_modal as dm
from sim_app.dash_app import app

import data_transfer

from sim_app.study_functions import prepare_initial_curve_computation, \
    prepare_curve_refinement_calculation
from tqdm import tqdm
from decimal import Decimal

tqdm.pandas()

# from pandarallel import pandarallel
# pandarallel.initialize()
# from multiprocesspandas import applyparallel

server = app.server

app._favicon = 'logo-zbt.ico'
app.title = 'PEMFC Model'

# Component Initialization & App layout
# ----------------------------------------

# Read layout settings from json file
with open(os.path.join('settings', 'parameters_layout.json')) as file:
    parameters_layout = json.load(file)

# New: Read layout settings from json file
# Initialize GUI
gui_settings_def_file = os.path.join('settings', "styling.yaml")
gui_settings, gui_conditions = dl_new.create_gui_from_definition_file(gui_settings_def_file)

# Process bar components
pbar = dbc.Progress(id='pbar')
timer_progress = dcc.Interval(id='timer_progress',
                              interval=15000)

app.layout = dbc.Container([
    dcc.Store(id="base_settings_data"),
    dcc.Store(id="input_data"),
    dcc.Store(id="df_input_data"),
    dbc.Spinner(dcc.Store(id='result_data_store'), fullscreen=True,
                spinner_class_name='loading_spinner',
                fullscreen_class_name='loading_spinner_bg'),
    dcc.Store(id='df_result_data_store'),
    dcc.Store(id='df_input_store'),
    dcc.Store(id='variation_parameter'),

    # Dummy div for initialization
    # (Read available input parameters, create study table)
    html.Div(id="initial_dummy"),

    # empty Div to trigger javascript file for graph resizing
    html.Div(id="output-clientside"),
    # modal for any warning
    dm.create_modal(),

    html.Div([  # HEADER (Header row, logo and title)
        html.Div(  # Logo
            html.Div(
                html.Img(
                    src=app.get_asset_url("logo-zbt.png"),
                    id="zbt-image",
                    style={"object-fit": 'contain',
                           'position': 'center',
                           "width": "auto",
                           "margin": "auto"}),
                id="logo-container", className="pretty_container h-100",
                style={'display': 'flex', 'justify-content': 'center',
                       'align-items': 'center'}
            ),
            className='col-12 col-lg-4 mb-2'
        ),
        html.Div(  # Title
            html.Div(
                html.H3("Fuel Cell Stack Model",
                        style={"margin": "auto",
                               "min-height": "47px",
                               "font-weight": "bold",
                               "-webkit-text-shadow-width": "1px",
                               "-webkit-text-shadow-color": "#aabad6",
                               "color": "#0062af",
                               "font-size": "40px",
                               "width": "auto",
                               "text-align": "center",
                               "vertical-align": "middle"}),
                className="pretty_container h-100", id="title",
                style={'justify-content': 'center', 'align-items': 'center',
                       'display': 'flex'}),
            style={'justify-content': 'space-evenly'},
            className='col-12 col-lg-8 mb-2'),
    ],
        id="header",
        className='row'
    ),

    html.Div([  # MIDDLE
        html.Div([  # LEFT MIDDLE / (Menu Column)
            # Menu Tabs
            # html.Div([
            #     dl.tab_container(parameters_layout)],
            #     id='setting_container'),

            # Add new input
            html.Div([gui_settings],
                     id='setting_container'),

            # Buttons 1 (Load/Save Settings, Run
            html.Div([  # LEFT MIDDLE: Buttons
                html.Div([
                    html.Div([
                        dcc.Upload(id='upload-file',
                                   children=html.Button(
                                       'Load Settings',
                                       id='load-button',
                                       className='settings_button',
                                       style={'display': 'flex'})),
                        dcc.Download(id="savefile-json"),
                        html.Button('Save Settings', id='save-button',
                                    className='settings_button',
                                    style={'display': 'flex'}),
                        html.Button('Run single Simulation', id='run_button',
                                    className='settings_button',
                                    style={'display': 'flex'})
                    ],

                        style={'display': 'flex',
                               'flex-wrap': 'wrap',
                               # 'flex-direction': 'column',
                               # 'margin': '5px',
                               'justify-content': 'space-evenly'}
                    )],
                    className='neat-spacing')], style={'flex': '1'},
                id='load_save_run', className='pretty_container'),
            # Buttons 2 (Curve)
            html.Div([  # LEFT MIDDLE: Buttons
                html.Div([
                    html.Div([
                        html.Button('Calc. Curve',
                                    id='btn_init_curve',
                                    className='settings_button',
                                    style={'display': 'flex'}),
                        html.Button('Refine Curve',
                                    id='btn_refine_curve',
                                    className='settings_button',
                                    style={'display': 'flex'}),
                    ],

                        style={'display': 'flex',
                               'flex-wrap': 'wrap',
                               # 'flex-direction': 'column',
                               # 'margin': '5px',
                               'justify-content': 'space-evenly'}
                    )],
                    className='neat-spacing')], style={'flex': '1'},
                id='multiple_runs', className='pretty_container'),
            # Buttons 3 (Study)
            html.Div([
                dcc.Markdown(
                    '''
                    ###### Parameter Study
                            
                    **Instruction**  The table below shows all parameter. For 
                    each parameter either percentual deviation
                    or multiple values can be given. Separate multiple values by 
                    comma. Column "Example" shows example input and is not used 
                    for calculation. 
                    Only numeric parameter implemented yet.
                            
                    The table can be exported, modified in Excel & uploaded. 
                    Reload GUI to restore table functionality after upload. 
                            
                    Below table, define study options.  
                    '''),
                html.Div(id="study_table"),
                dcc.Upload(
                    id='datatable-upload',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select Files')
                    ]),
                    style={
                        'width': '90%', 'height': '40px', 'lineHeight': '40px',
                        'borderWidth': '1px', 'borderStyle': 'dashed',
                        'borderRadius': '5px', 'textAlign': 'center',
                        'margin': '10px'
                    },
                ),
                html.Div(
                    dbc.Checklist(
                        id="check_calc_curve",
                        options=[{'label': 'Calc. Current-Voltage Curve',
                                  'value': 'calc_curve'}])),
                html.Div(
                    dbc.RadioItems(
                        id="check_study_type",
                        options=[{'label': 'Single Variation',
                                  'value': 'single'},
                                 {'label': 'Full Factorial',
                                  'value': 'full'}],
                        value='single',
                        inline=True)),
                html.Div([
                    html.Div([
                        html.Button('Run Study', id='btn_study',
                                    className='settings_button',
                                    style={'display': 'flex'}),
                    ],
                        style={'display': 'flex',
                               'flex-wrap': 'wrap',
                               'justify-content': 'space-evenly'}
                    )],
                    className='neat-spacing')], style={'flex': '1'},
                id='study', className='pretty_container'),

            # Buttons 4 (Save Results, Load Results, Update Plot (debug))
            html.Div([  # LEFT MIDDLE: Buttons
                html.Div([
                    html.Div(
                        [html.Button('Plot', id='btn_plot',
                                     className='settings_button',
                                     style={'display': 'flex'}),
                         html.Button('Save Results', id='btn_save_res',
                                     className='settings_button',
                                     style={'display': 'flex'}),
                         dcc.Download(id="download-results"),

                         dcc.Upload(
                             id='load_res',
                             children=html.Button(
                                 'Load Results', id='btn_load_res',
                                 className='settings_button',
                                 style={'display': 'flex'}))],
                        style={'display': 'flex',
                               'flex-wrap': 'wrap',
                               'justify-content': 'space-evenly'}
                    )],
                    className='neat-spacing')], style={'flex': '1'},
                id='save_load_res', className='pretty_container'),
            html.Div([  # LEFT MIDDLE: Spinner
                html.Div(
                    [html.Div(
                        [dbc.Spinner(html.Div(id="spinner_run_single")),
                         dbc.Spinner(html.Div(id="spinner_curve")),
                         dbc.Spinner(html.Div(id="spinner_curve_refine")),
                         dbc.Spinner(html.Div(id="spinner_study"))],

                        # style={'display': 'flex',
                        #       'flex-wrap': 'wrap',
                        #       'justify-content': 'space-evenly'}
                    )],
                    className='neat-spacing')],
                style={'flex': '1'},
                id='spinner_bar',
                className='pretty_container'),
            # Progress Bar
            html.Div([
                # See: https://towardsdatascience.com/long-callbacks-in-dash-web-apps-72fd8de25937
                html.Div([
                    html.Div([pbar, timer_progress])],
                    className='neat-spacing')], style={'flex': '1'},
                id='progress_bar', className='pretty_container')],
            id="left-column", className='col-12 col-lg-4 mb-2'),
        html.Div([  # RIGHT MIDDLE  (Result Column)
            html.Div(
                [html.Div('Current-Voltage Curve', className='title'),
                 dcc.Graph(id='curve_graph')],
                id='div_curve_graph',
                className='pretty_container',
                style={'overflow': 'auto'}),
            html.Div(
                [html.Div('Global Results (for Study only first dataset shown)',
                          className='title'),
                 dt.DataTable(id='global_data_table',
                              editable=True,
                              column_selectable='multi')],
                id='div_global_table',
                className='pretty_container',
                style={'overflow': 'auto'}),
            html.Div([
                html.Div('Heatmap', className='title'),
                html.Div(
                    [html.Div(
                        dcc.Dropdown(
                            id='dropdown_heatmap',
                            placeholder='Select Variable',
                            className='dropdown_input'),
                        id='div_results_dropdown',
                        # style={'padding': '1px', 'min-width': '200px'}
                    ),
                        html.Div(
                            dcc.Dropdown(id='dropdown_heatmap_2',
                                         className='dropdown_input',
                                         style={'visibility': 'hidden'}),
                            id='div_results_dropdown_2', )],
                    style={'display': 'flex',
                           'flex-direction': 'row',
                           'flex-wrap': 'wrap',
                           'justify-content': 'left'}),
                # RIGHT MIDDLE BOTTOM
                dbc.Spinner(dcc.Graph(id="heatmap_graph"),
                            spinner_class_name='loading_spinner',
                            fullscreen_class_name='loading_spinner_bg')],
                id='heatmap_container',
                className='graph pretty_container'),
            html.Div([
                html.Div('Plots', className='title'),
                html.Div(
                    [html.Div(
                        dcc.Dropdown(
                            id='dropdown_line',
                            placeholder='Select Variable',
                            className='dropdown_input'),
                        id='div_dropdown_line',
                        # style={'padding': '1px', 'min-width': '200px'}
                    ),
                        html.Div(
                            dcc.Dropdown(id='dropdown_line2',
                                         className='dropdown_input',
                                         style={'visibility': 'hidden'}),
                            id='div_dropdown_line_2',
                            # style={'padding': '1px', 'min-width': '200px'}
                        )],
                    style={'display': 'flex', 'flex-direction': 'row',
                           'flex-wrap': 'wrap',
                           'justify-content': 'left'},
                ),
                html.Div([
                    html.Div(
                        [dcc.Store(id='append_check'),
                         html.Div(
                             [html.Div(
                                 children=dbc.DropdownMenu(
                                     id='checklist_dropdown',
                                     children=[
                                         dbc.Checklist(
                                             id='data_checklist',
                                             # input_checked_class_name='checkbox',
                                             style={'max-height': '400px',
                                                    'overflow': 'auto'})],
                                     toggle_style={
                                         'textTransform': 'none',
                                         'background': '#fff',
                                         'border': '#ccc',
                                         'letter-spacing': '0',
                                         'font-size': '11px'},
                                     align_end=True,
                                     toggle_class_name='dropdown_input',
                                     label="Select Cells"), ),
                                 html.Button('Clear All', id='clear_all_button',
                                             className='local_data_buttons'),
                                 html.Button('Select All',
                                             id='select_all_button',
                                             className='local_data_buttons')],
                             style={'display': 'flex',
                                    'flex-wrap': 'wrap',
                                    'margin-bottom': '5px'})],
                        # style={'width': '200px'}
                    ),
                    dcc.Store(id='cells_data')],
                    style={'display': 'flex', 'flex-direction': 'column',
                           'justify-content': 'left'}),
                dbc.Spinner(dcc.Graph(id='line_graph'),
                            spinner_class_name='loading_spinner',
                            fullscreen_class_name='loading_spinner_bg')],
                className="pretty_container",
                style={'display': 'flex',
                       'flex-direction': 'column',
                       'justify-content': 'space-evenly'}
            )],
            id='right-column', className='col-12 col-lg-8 mb-2')],
        className="row",
        style={'justify-content': 'space-evenly'}),

    # Bottom row, links to GitHub,...
    html.Div(
        html.Div(
            [html.A('Source code:'),
             html.A('web interface',
                    href='https://www.github.com/zbt-tools/simulation-web-app-template',
                    target="_blank")],
            id='github_links',
            style={'overflow': 'auto',
                   'position': 'relative',
                   'justify-content': 'space-evenly',
                   'align-items': 'center',
                   'min-width': '30%',
                   'display': 'flex'}),
        id='link_container',
        style={'overflow': 'auto',
               'position': 'relative',
               'justify-content': 'center',
               'align-items': 'center',
               'display': 'flex'},
        className='pretty_container')
],
    id="mainContainer",
    # className='twelve columns',
    fluid=True,
    style={'padding': '0px'})


@app.callback(
    Output('pbar', 'value'),
    Output('pbar', 'label'),
    Output('pbar', 'color'),
    Input('timer_progress', 'n_intervals'),
    prevent_initial_call=True)
def cbf_progress_bar(*args) -> (float, str):
    """
    # https://towardsdatascience.com/long-callbacks-in-dash-web-apps-72fd8de25937
    """

    try:
        with open('progress.txt', 'r') as file:
            str_raw = file.read()
        last_line = list(filter(None, str_raw.split('\n')))[-1]
        percent = float(last_line.split('%')[0])
    except:
        percent = 0
    finally:
        text = f'{percent:.0f}%'
        if int(percent) == 100:
            color = "success"
        else:
            color = "primary"
        return percent, text, color


@app.callback(
    Output({'type': 'new_input', 'sim_id': ALL}, 'value'),
    Output("base_settings_data", "data"),
    Output('df_input_store', 'data'),
    Output("study_table", "children"),
    Input("initial_dummy", "children"),
    State({'type': 'new_input', 'sim_id': ALL}, 'value'))
def cbf_initialization(dummy, gui_value_list: list):
    """
    Initialization
    """

    # Read default settings.json file from sim_base_dir & local settings.json
    # --------------------------------------
    try:
        # Initially get default simulation settings structure from
        # settings.json file in pemfc core module
        # sim_base_dir = os.path.dirname(pemfc.__file__)
        sim_base_dir = '.'
        with open(os.path.join(sim_base_dir, 'settings', 'settings.json')) as file:
            base_settings = json.load(file)
            base_settings = df.convert_to_storage_format(base_settings)
    except Exception as E:
        print(repr(E))

    try:
        # Initially get default simulation input values from local
        # settings.json file
        with open(os.path.join('settings', 'settings.json')) as file:
            input_settings = json.load(file)
    except Exception as E:
        print(repr(E))

    settings_file_dict, _ = df.settings_to_dash_gui(input_settings)

    # From input field to simulation structure...
    # --------------------------------------
    gui_settings_dict = df.convert_gui_state_to_sim_dict(ctx.states_list[0])

    # Update gui_settings data with default settings
    # --------------------------------------
    initialized_gui_settings_dict = df.update_gui_settings_dict(settings_file_dict,
                                                                gui_settings_dict)

    # And back from simulation structure to gui input field list...
    # --------------------------------------
    gui_return_value_list = df.convert_sim_dict_to_state_value_list(initialized_gui_settings_dict,
                                                                    ctx.states_list[0])

    # Save initial data in input DataDrame
    # --------------------------------------
    # Save initialized input data in DataFrame
    # (one row "nominal")
    df_input = df.convert_gui_settings_to_DataFrame(initialized_gui_settings_dict)
    df_input_store = df.convert_to_storage_format(df_input)

    # Initialize study data table
    # -------------------------------------
    # Info: css stylesheet needed to be updated to show dropdown, see
    # https://community.plotly.com/t/resolved-dropdown-options-in-datatable-not-showing/20366/4

    # Dummy input
    empty_study_table = pd.DataFrame(dict([
        ('Parameter', list(df_input.columns)),
        ('Example', [str(x) for x in list(df_input.loc["nominal"])]),
        ('Variation Type', len(df_input.columns) * [None]),
        ('Values', len(df_input.columns) * [None])

        # ('ValueType', ["float", None, None, None])
    ]))

    table = dash_table.DataTable(
        id='study_data_table',
        style_data={
            'whiteSpace': 'normal',
            'height': 'auto',
            'lineHeight': '15px'
        },
        data=empty_study_table.to_dict('records'),
        columns=[
            {'id': 'Parameter', 'name': 'Parameter', 'editable': False},
            {'id': 'Example', 'name': 'Example', 'editable': False},
            {'id': 'Variation Type', 'name': 'Variation Type',
             'presentation': 'dropdown'},
            {'id': 'Values', 'name': 'Values'},
        ],

        editable=True,
        dropdown={
            'Variation Type': {
                'options': [
                    {'label': i, 'value': i}
                    for i in ["Values", "Percent (+/-)"]
                ]},
        },
        filter_action="native",
        sort_action="native",
        page_action='none',
        export_format='xlsx',
        export_headers='display',
        style_table={'height': '300px', 'overflowY': 'auto'}
    )

    return gui_return_value_list, base_settings, df_input_store, table


@app.callback(
    [Output({'type': 'new_input', 'sim_id': ALL}, 'value'),
     Output('upload-file', 'contents'),
     Output('modal-title', 'children'),
     Output('modal-body', 'children'),
     Output('modal', 'is_open')],
    Input('upload-file', 'contents'),
    [State('upload-file', 'filename'),
     State({'type': 'new_input', 'sim_id': ALL}, 'value'),
     State('modal', 'is_open')])
def cbf_load_settings(contents, filename, gui_value_list,
                      modal_state):
    if contents is None:
        raise PreventUpdate
    else:
        if 'json' in filename:
            try:
                settings_dict = df.parse_contents(contents, filename,
                                                  dtype=dict)

                gui_label_value_dict, error_list = \
                    df.settings_to_dash_gui_format(settings_dict)

                new_value_list, new_multivalue_list = \
                    df.update_gui_lists(gui_label_value_dict,
                                        value, multival, ids, ids_multival)

                if not error_list:
                    # All JSON settings match Dash IDs
                    modal_title, modal_body = dm.modal_process('loaded')
                    return new_value_list, new_multivalue_list, \
                        None, modal_title, modal_body, not modal_state
                else:
                    # Some JSON settings do not match Dash IDs; return values
                    # that matched with Dash IDs
                    modal_title, modal_body = \
                        dm.modal_process('id-not-loaded', error_list)
                    return new_value_list, new_multivalue_list, \
                        None, modal_title, modal_body, not modal_state
            except Exception as E:
                # Error / JSON file cannot be processed; return old value
                modal_title, modal_body = \
                    dm.modal_process('error', error=repr(E))
                return value, multival, None, modal_title, modal_body, \
                    not modal_state
        else:
            # Not JSON file; return old value
            modal_title, modal_body = dm.modal_process('wrong-file')
            return value, multival, None, modal_title, modal_body, \
                not modal_state


@app.callback(
    [Output("savefile-json", "data")],
    Input('save-button', "n_clicks"),
    [State({'type': 'input', 'id': ALL, 'specifier': ALL}, 'value'),
     State({'type': 'multiinput', 'id': ALL, 'specifier': ALL}, 'value'),
     State({'type': 'input', 'id': ALL, 'specifier': ALL}, 'id'),
     State({'type': 'multiinput', 'id': ALL, 'specifier': ALL}, 'id')],
    prevent_initial_call=True,
)
def cbf_save_settings(n_clicks, val1, val2, ids, ids2):
    """

    @param n_clicks:
    @param val1:
    @param val2:
    @param ids:
    @param ids2:
    @return:
    """
    save_complete = True

    dict_data = df.process_inputs(val1, val2, ids, ids2)  # values first

    if not save_complete:  # ... save only GUI inputs
        sep_id_list = [joined_id.split('-') for joined_id in
                       dict_data.keys()]

        val_list = dict_data.values()
        new_dict = {}
        for sep_id, vals in zip(sep_id_list, val_list):
            current_level = new_dict
            for id_l in sep_id:
                if id_l not in current_level:
                    if id_l != sep_id[-1]:
                        current_level[id_l] = {}
                    else:
                        current_level[id_l] = vals
                current_level = current_level[id_l]

        return dict(content=json.dumps(new_dict, sort_keys=True, indent=2),
                    filename='settings.json')

    else:  # ... save complete settings as passed to pemfc simulation

        # code portion of generate_inputs()
        # ------------------------
        input_data = {}
        for k, v in dict_data.items():
            input_data[k] = {'sim_name': k.split('-'), 'value': v}

        # code portion of run_simulation()
        # ------------------------

        with open(os.path.join('settings', 'settings.json')) \
                as file:
            settings = json.load(file)
        settings, _ = data_transfer.dict_transfer(input_data, settings)

        return dict(content=json.dumps(settings, indent=2),
                    filename='settings.json')


@app.callback(
    Output('df_result_data_store', 'data'),
    Output('df_input_store', 'data'),
    Output("spinner_run_single", 'children'),
    Input("run_button", "n_clicks"),
    [State({'type': 'input', 'id': ALL, 'specifier': ALL}, 'value'),
     State({'type': 'multiinput', 'id': ALL, 'specifier': ALL}, 'value'),
     State({'type': 'input', 'id': ALL, 'specifier': ALL}, 'id'),
     State({'type': 'multiinput', 'id': ALL, 'specifier': ALL}, 'id'),
     State("base_settings_data", "data")],
    prevent_initial_call=True)
def cbf_run_single_cal(n_click, inputs, inputs2, ids, ids2, settings):
    """
    Changelog:

    """
    try:
        # Read pemfc settings.json from store
        settings = df.read_data(settings)

        # Read data from input fields and save input in dict/dataframe
        # (one row "nominal")
        df_input = df.process_inputs(inputs, inputs2, ids, ids2,
                                     dtype=pd.DataFrame)
        df_input_raw = df_input.copy()

        # Create complete setting dict, append it in additional column
        # "settings" to df_input
        df_input = create_settings(df_input, settings)

        # Run simulation
        df_result, _ = df.run_simulation(df_input)

        # Save results
        df_result_store = df.convert_to_storage_format(df_result)
        df_input_store = df.convert_to_storage_format(df_input_raw)

        return df_result_store, df_input_store, ""

    except Exception as E:
        modal_title, modal_body = \
            dm.modal_process('input-error', error=repr(E))


@app.callback(Output('study_data_table', 'data'),
              Output('study_data_table', 'columns'),
              Input('datatable-upload', 'contents'),
              State('datatable-upload', 'filename'),
              prevent_initial_call=True)
def cbf_update_studytable(contents, filename):
    if contents is None:
        return [{}], []
    data = df.parse_contents(contents, filename, dtype=pd.DataFrame)
    return data.to_dict('records'), [{"name": i, "id": i} for i in data.columns]


@app.callback(
    Output('df_result_data_store', 'data'),
    Output('df_input_store', 'data'),
    Output('spinner_study', 'children'),
    Input("btn_study", "n_clicks"),
    [State({'type': 'input', 'id': ALL, 'specifier': ALL}, 'value'),
     State({'type': 'multiinput', 'id': ALL, 'specifier': ALL}, 'value'),
     State({'type': 'input', 'id': ALL, 'specifier': ALL}, 'id'),
     State({'type': 'multiinput', 'id': ALL, 'specifier': ALL}, 'id')],
    State("base_settings_data", "data"),
    State("study_data_table", "data"),
    State("check_calc_curve", "value"),
    State("check_study_type", "value"),
    prevent_initial_call=True)
def cbf_run_study(btn, inputs, inputs2, ids, ids2, settings, tabledata,
                  check_calc_curve, check_study_type):
    """
    #ToDO Documentation

    Arguments
    ----------
    settings
    tabledata
    check_calc_curve:    Checkbox, if complete
    check_study_type:
    """
    variation_mode = "dash_table"

    # Calculation of polarization curve for each dataset?
    if isinstance(check_calc_curve, list):
        if "calc_curve" in check_calc_curve:
            curve_calculation = True
        else:
            curve_calculation = False
    else:
        curve_calculation = False
    n_refinements = 15

    mode = check_study_type

    # Progress bar init
    std_err_backup = sys.stderr
    file_prog = open('progress.txt', 'w')
    sys.stderr = file_prog

    # Read pemfc settings.json from store
    settings = df.read_data(settings)

    # Read data from input fields and save input in dict (legacy)
    # / pd.DataDrame (one row with index "nominal")
    df_input = df.process_inputs(
        inputs, inputs2, ids, ids2, dtype=pd.DataFrame)
    df_input_backup = df_input.copy()

    # Create multiple parameter sets
    if variation_mode == "dash_table":
        data = df.variation_parameter(
            df_input, keep_nominal=False, mode=mode, table_input=tabledata)
    else:
        raise NotImplementedError
    varpars = list(data["variation_parameter"].unique())

    if not curve_calculation:
        # Create complete setting dict & append it in additional column
        # "settings" to df_input
        data = create_settings(data, settings, input_cols=df_input.columns)
        # Run Simulation
        results, success = df.run_simulation(data)
        results = df.convert_to_storage_format(results)

    else:  # ... calculate pol. curve for each parameter set
        result_data = pd.DataFrame(columns=data.columns)

        # grouped_data = data.groupby(varpars, sort=False)
        # for _, group in grouped_data:
        for i in range(0, len(data)):
            # Ensure DataFrame with double bracket
            # https://stackoverflow.com/questions/20383647/pandas-selecting-by-label-sometimes-return-series-sometimes-returns-dataframe
            # df_input_single = df_input.loc[[:], :]

            # max_i = find_max_current_density(data.iloc[[i]], df_input, settings)
            max_i = 10000  # dummy value
            # # Reset solver settings
            # df_input = df_input_backup.copy()

            success = False
            while (not success) and (max_i > 5000):
                # Prepare & calculate initial points
                df_results = prepare_initial_curve_computation(
                    input_df=data.iloc[[i]], i_limits=[1, max_i],
                    settings=settings, input_cols=df_input.columns)
                df_results, success = df.run_simulation(df_results)
                max_i -= 2000

            if not success:
                continue

                # First refinement steps
            for _ in range(n_refinements):
                df_refine = prepare_curve_refinement_calculation(
                    input_df=df_input, data_df=df_results, settings=settings)
                df_refine, success = df.run_simulation(
                    df_refine, return_unsuccessful=False)
                df_results = pd.concat(
                    [df_results, df_refine], ignore_index=True)

            result_data = pd.concat([result_data, df_results], ignore_index=True)

        results = df.store_data(result_data)

    df_input_store = df.store_data(df_input_backup)

    file_prog.close()
    sys.stderr = std_err_backup

    return results, df_input_store, "."


@app.callback(
    Output("download-results", "data"),
    Input("btn_save_res", "n_clicks"),
    State('df_result_data_store', 'data'),
    prevent_initial_call=True)
def cbf_save_results(inp, state):
    # State-Store access returns None, I don't know why (FKL)
    data = ctx.states["df_result_data_store.data"]
    with open('results.pickle', 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return dcc.send_file("results.pickle")


@app.callback(
    Output('df_result_data_store', 'data'),
    Input("load_res", "contents"),
    prevent_initial_call=True)
def cbf_load_results(content):
    # https://dash.plotly.com/dash-core-components/upload
    content_type, content_string = content.split(',')
    decoded = base64.b64decode(content_string)
    b = pickle.load(io.BytesIO(decoded))
    return b


@app.callback(
    [Output('global_data_table', 'columns'),
     Output('global_data_table', 'data'),
     Output('global_data_table', 'export_format')],
    Input('df_result_data_store', 'data'),
    prevent_initial_call=True
)
def global_outputs_table(*args):
    """
    ToDo: Add additional input.
    If storage triggered callback, use first result row,
    if dropdown triggered callback, select this row.
    """

    # Read results
    results = df.read_data(ctx.inputs["df_result_data_store.data"])

    result_set = results.iloc[0]

    global_result_dict = result_set["global_data"]
    names = list(global_result_dict.keys())
    values = [f"{v['value']:.3e}" for k, v in global_result_dict.items()]
    units = [v['units'] for k, v in global_result_dict.items()]

    column_names = ['Quantity', 'Value', 'Units']
    columns = [{'deletable': True, 'renamable': True,
                'selectable': True, 'name': col, 'id': col}
               for col in column_names]
    datas = [{column_names[0]: names[i],
              column_names[1]: values[i],
              column_names[2]: units[i]} for i in range(len(values))]

    return columns, datas, 'csv',


@app.callback(
    [Output('dropdown_heatmap', 'options'),
     Output('dropdown_heatmap', 'value')],
    Input('df_result_data_store', 'data'),
    prevent_initial_call=True
)
def get_dropdown_options_heatmap(results):
    """
    ToDo: Add additional input.
    If storage triggered callback, use first result row,
    if dropdown triggered callback, select this row.
    """

    # Read results
    results = df.read_data(ctx.inputs["df_result_data_store.data"])

    result_set = results.iloc[0]

    local_data = result_set["local_data"]
    values = [{'label': key, 'value': key} for key in local_data
              if 'xkey' in local_data[key]]
    return values, values[0]['value']


@app.callback(
    [Output('dropdown_line', 'options'),
     Output('dropdown_line', 'value')],
    Input('df_result_data_store', 'data'),
    prevent_initial_call=True
)
def get_dropdown_options_line_graph(results):
    """
    ToDo: Add additional input.
    If storage triggered callback, use first result row,
    if dropdown triggered callback, select this row.
    """

    # Read results
    results = df.read_data(ctx.inputs["df_result_data_store.data"])

    result_set = results.iloc[0]

    local_data = result_set["local_data"]
    values = [{'label': key, 'value': key} for key in local_data]
    return values, values[0]['value']


@app.callback(
    [Output('dropdown_heatmap_2', 'options'),
     Output('dropdown_heatmap_2', 'value'),
     Output('dropdown_heatmap_2', 'style')],
    [Input('dropdown_heatmap', 'value'),
     Input('df_result_data_store', 'data')]
)
def get_dropdown_options_heatmap_2(dropdown_key, results):
    if dropdown_key is None or results is None:
        raise PreventUpdate
    else:
        # Read results
        results = df.read_data(ctx.inputs["df_result_data_store.data"])

        result_set = results.iloc[0]
        local_data = result_set["local_data"]
        if 'value' in local_data[dropdown_key]:
            return [], None, {'visibility': 'hidden'}
        else:
            options = [{'label': key, 'value': key} for key in
                       local_data[dropdown_key]]
            value = options[0]['value']
            return options, value, {'visibility': 'visible'}


@app.callback(
    [Output('dropdown_line2', 'options'),
     Output('dropdown_line2', 'value'),
     Output('dropdown_line2', 'style')],
    Input('dropdown_line', 'value'),
    Input('df_result_data_store', 'data'),
    prevent_initial_call=True
)
def get_dropdown_options_line_graph_2(dropdown_key, results):
    if dropdown_key is None or results is None:
        raise PreventUpdate
    else:
        # Read results
        results = df.read_data(ctx.inputs["df_result_data_store.data"])

        result_set = results.iloc[0]

        local_data = result_set["local_data"]
        if 'value' in local_data[dropdown_key]:
            return [], None, {'visibility': 'hidden'}
        else:
            options = [{'label': key, 'value': key} for key in
                       local_data[dropdown_key]]
            value = options[0]['value']
            return options, value, {'visibility': 'visible'}


@app.callback(
    Output("heatmap_graph", "figure"),
    [Input('dropdown_heatmap', 'value'),
     Input('dropdown_heatmap_2', 'value')],
    Input('df_result_data_store', 'data'),
    prevent_initial_call=True
)
def update_heatmap_graph(dropdown_key, dropdown_key_2, results):
    if dropdown_key is None or results is None:
        raise PreventUpdate
    else:
        # Read results
        results = df.read_data(ctx.inputs["df_result_data_store.data"])

        result_set = results.iloc[0]

        local_data = result_set["local_data"]

        if 'value' in local_data[dropdown_key]:
            zvalues = local_data[dropdown_key]['value']
        elif dropdown_key_2 is not None:
            zvalues = local_data[dropdown_key][dropdown_key_2]['value']
        else:
            raise PreventUpdate

        x_key = local_data[dropdown_key]['xkey']
        y_key = 'Cells'
        xvalues = np.asarray(local_data[x_key]['value'])
        if xvalues.ndim > 1:
            xvalues = xvalues[0]
        yvalues = np.asarray(local_data[y_key]['value'])
        if yvalues.ndim > 1:
            yvalues = yvalues[0]

        n_y = len(yvalues)
        n_x = xvalues.shape[-1]
        n_z = yvalues.shape[-1]

        if n_x == n_z + 1:
            xvalues = df.interpolate_1d(xvalues)

        if dropdown_key_2 is None:
            z_title = dropdown_key + ' / ' + local_data[dropdown_key]['units']
        else:
            z_title = dropdown_key + ' / ' \
                      + local_data[dropdown_key][dropdown_key_2]['units']

        height = 800
        # width = 500

        font_props = dl.graph_font_props

        base_axis_dict = \
            {'tickfont': font_props['medium'],
             'titlefont': font_props['large'],
             'title': x_key + ' / ' + local_data[x_key]['units'],
             'tickmode': 'array', 'showgrid': True}

        tick_division_dict = \
            {'fine': {'upper_limit': 10, 'value': 1},
             'medium': {'upper_limit': 20, 'value': 2},
             'medium_coarse': {'upper_limit': 50, 'value': 5},
             'coarse': {'value': 10}}

        def filter_tick_text(data, spacing=1):
            return [str(data[i]) if i % spacing == 0 else ' '
                    for i in range(len(data))]

        def granular_tick_division(data, division=None):
            n = len(data)
            if division is None:
                division = tick_division_dict
            if n <= division['fine']['upper_limit']:
                result = filter_tick_text(data, division['fine']['value'])
            elif division['fine']['upper_limit'] < n \
                    <= division['medium']['upper_limit']:
                result = \
                    filter_tick_text(data, division['medium']['value'])
            elif division['medium']['upper_limit'] < n \
                    <= division['medium_coarse']['upper_limit']:
                result = filter_tick_text(
                    data, division['medium_coarse']['value'])
            else:
                result = \
                    filter_tick_text(data, division['coarse']['value'])
            return result

        # y_tick_labels[-1] = str(n_y - 1)

        x_axis_dict = copy.deepcopy(base_axis_dict)
        x_axis_dict['title'] = x_key + ' / ' + local_data[x_key]['units']
        x_axis_dict['tickvals'] = local_data[x_key]['value']
        x_axis_dict['ticktext'] = \
            granular_tick_division(local_data[x_key]['value'])

        y_axis_dict = copy.deepcopy(base_axis_dict)
        y_axis_dict['title'] = y_key + ' / ' + local_data[y_key]['units']
        y_axis_dict['tickvals'] = yvalues
        y_axis_dict['ticktext'] = granular_tick_division(range(n_y))

        z_axis_dict = copy.deepcopy(base_axis_dict)
        z_axis_dict['title'] = z_title
        # z_axis_dict['tickvals'] = zvalues

        layout = go.Layout(
            font=font_props['large'],
            # title='Local Results in Heat Map',
            titlefont=font_props['large'],
            xaxis=x_axis_dict,
            yaxis=y_axis_dict,
            margin={'l': 75, 'r': 20, 't': 10, 'b': 20},
            height=height
        )
        scene = dict(
            xaxis=x_axis_dict,
            yaxis=y_axis_dict,
            zaxis=z_axis_dict)

        heatmap = \
            go.Surface(z=zvalues, x=xvalues, y=yvalues,  # xgap=1, ygap=1,
                       colorbar={
                           'tickfont': font_props['large'],
                           'title': {
                               'text': z_title,
                               'font': {'size': font_props['large']['size']},
                               'side': 'right'},
                           # 'height': height - 300
                           'lenmode': 'fraction',
                           'len': 0.75
                       })

        fig = go.Figure(data=heatmap, layout=layout)
        fig.update_layout(scene=scene)

    return fig


@app.callback(
    [Output('line_graph', 'figure'),
     Output('cells_data', 'data'),
     Output('data_checklist', 'options'),
     Output('data_checklist', 'value')],
    [Input('dropdown_line', 'value'),
     Input('dropdown_line2', 'value'),
     Input('data_checklist', 'value'),
     Input('select_all_button', 'n_clicks'),
     Input('clear_all_button', 'n_clicks'),
     Input('line_graph', 'restyleData')],
    Input('df_result_data_store', 'data'),
    prevent_initial_call=True
)
def update_line_graph(drop1, drop2, checklist, select_all_clicks,
                      clear_all_clicks, restyle_data, results):
    ctx_triggered = dash.callback_context.triggered[0]['prop_id']
    if drop1 is None or results is None:
        raise PreventUpdate
    else:
        # Read results
        results = df.read_data(ctx.inputs["df_result_data_store.data"])

        result_set = results.iloc[0]

        local_data = result_set["local_data"]

        fig = go.Figure()

        default_x_key = 'Number'
        x_key = local_data[drop1].get('xkey', default_x_key)

        if drop2 is None:
            y_title = drop1 + ' / ' + local_data[drop1]['units']
        else:
            y_title = drop1 + ' - ' + drop2 + ' / ' \
                      + local_data[drop1][drop2]['units']

        if x_key == default_x_key:
            x_title = x_key + ' / -'
        else:
            x_title = x_key + ' / ' + local_data[x_key]['units']

        if 'Error' in y_title:
            y_scale = 'log'
        else:
            y_scale = 'linear'

        layout = go.Layout(
            font={'color': 'black', 'family': 'Arial'},
            # title='Local Results in Heat Map',
            titlefont={'size': 11, 'color': 'black'},
            xaxis={'tickfont': {'size': 11}, 'titlefont': {'size': 14},
                   'title': x_title},
            yaxis={'tickfont': {'size': 11}, 'titlefont': {'size': 14},
                   'title': y_title},
            margin={'l': 100, 'r': 20, 't': 20, 'b': 20},
            yaxis_type=y_scale)

        fig.update_layout(layout)

        if 'value' in local_data[drop1]:
            yvalues = np.asarray(local_data[drop1]['value'])
        elif drop2 is not None:
            yvalues = np.asarray(local_data[drop1][drop2]['value'])
        else:
            raise PreventUpdate

        n_y = np.asarray(yvalues).shape[-1]
        if x_key in local_data:
            xvalues = np.asarray(local_data[x_key]['value'])
            if len(xvalues) == n_y + 1:
                xvalues = df.interpolate_1d(xvalues)
        else:
            xvalues = np.asarray(list(range(n_y)))

        if xvalues.ndim > 1:
            xvalues = xvalues[0]

        if yvalues.ndim == 1:
            yvalues = [yvalues]
        cells = {}
        for num, yval in enumerate(yvalues):
            fig.add_trace(go.Scatter(x=xvalues, y=yval,
                                     mode='lines+markers',
                                     name='Cell {}'.format(num)))
            cells[num] = {'name': 'Cell {}'.format(num), 'data': yval}

        options = [{'label': cells[k]['name'], 'value': cells[k]['name']}
                   for k in cells]
        value = ['Cell {}'.format(str(i)) for i in range(n_y)]

        if checklist is None:
            return fig, cells, options, value
        else:
            if 'clear_all_button.n_clicks' in ctx_triggered:
                fig.for_each_trace(
                    lambda trace: trace.update(visible='legendonly'))
                return fig, cells, options, []
            elif 'data_checklist.value' in ctx_triggered:
                fig.for_each_trace(
                    lambda trace: trace.update(
                        visible=True) if trace.name in checklist
                    else trace.update(visible='legendonly'))
                return fig, cells, options, checklist
            elif 'line_graph.restyleData' in ctx_triggered:
                read = restyle_data[0]['visible']
                if len(read) == 1:
                    cell_name = cells[restyle_data[1][0]]['name']
                    if read[0] is True:  # lose (legendonly)
                        checklist.append(cell_name)
                    else:
                        if cell_name in checklist:
                            checklist.remove(cell_name)
                    value = [val for val in value if val in checklist]
                else:
                    value = [value[i] for i in range(n_y)
                             if read[i] is True]
                fig.for_each_trace(
                    lambda trace: trace.update(
                        visible=True) if trace.name in value
                    else trace.update(visible='legendonly'))
                # fig.plotly_restyle(restyle_data[0])
                return fig, cells, options, value
            else:
                return fig, cells, options, value


@app.callback(
    Output({'type': ALL, 'id': ALL, 'specifier': 'disable_basewidth'},
           'disabled'),
    Input({'type': ALL, 'id': ALL, 'specifier': 'dropdown_activate_basewidth'},
          'value'))
def disabled_callback(value):
    for num, val in enumerate(value):
        if val == "trapezoidal":
            value[num] = False
        else:
            value[num] = True
    return value


# @app.callback(
#     Output({'type': ALL, 'id': ALL, 'specifier': 'disabled_manifolds'},
#            'disabled'),
#     Input({'type': ALL, 'id': ALL,
#            'specifier': 'checklist_activate_calculation'}, 'value'),
#     Input({'type': ALL, 'id': ALL, 'specifier': 'disabled_manifolds'}, 'value'),
# )
# def activate_column(input1, input2):
#     len_state = len(input2)
#     list_state = [True for x in range(len_state)]  # disable=True for all inputs
#     for num, val in enumerate(input1):  # 3 inputs in input1 for 3 rows
#         if val == [1]:
#             list_state[0 + num] = list_state[3 + num] = list_state[15 + num] = \
#                 list_state[18 + num] = list_state[30 + num] = False
#             if input2[3 + num] == 'circular':
#                 list_state[6 + num], list_state[9 + num], list_state[12 + num] = \
#                     False, True, True
#             else:
#                 list_state[6 + num], list_state[9 + num], list_state[12 + num] = \
#                     True, False, False
#             if input2[18 + num] == 'circular':
#                 list_state[21 + num], list_state[24 + num], list_state[27 + num] = \
#                     False, True, True
#             else:
#                 list_state[21 + num], list_state[24 + num], list_state[27 + num] = \
#                     True, False, False
#     return list_state


# @app.callback(
#     Output({'type': 'container', 'id': ALL, 'specifier': 'disabled_cooling'},
#            'style'),
#     Input({'type': ALL, 'id': ALL, 'specifier':
#            'checklist_activate_cooling'}, 'value'),
#     State({'type': 'container', 'id': ALL, 'specifier': 'disabled_cooling'},
#           'id'),
#     State({'type': 'container', 'id': ALL, 'specifier': 'disabled_cooling'},
#           'style')
# )
# def disabled_cooling(input1, ids, styles):
#     len_val = len(ids)
#
#     new_styles = {'pointer-events': 'none', 'opacity': '0.4'}
#
#     if input1[0] == [1]:
#         list_state = [{}] * len_val
#     else:
#         list_state = [new_styles] * len_val
#     return list_state


@app.callback(
    Output({'type': 'container', 'id': ALL, 'specifier': 'visibility'},
           'style'),
    Input({'type': 'input', 'id': ALL, 'specifier': 'dropdown_activate'},
          'value'),
    State({'type': 'input', 'id': ALL, 'specifier': 'dropdown_activate'},
          'options')
)
def visibility(inputs, options):
    list_options = []
    for opt in options:
        list_options.extend([inside['value'] for inside in opt])
        # [[opt1, opt2],[opt3, opt4, opt5]] turns into
        # [opt1, opt2, opt3, opt4, opt5]

    for inp in inputs:
        #  Eliminate/replace chosen value with 'chose' for later
        list_options = \
            list(map(lambda item: item.replace(inp, 'chosen'),
                     list_options))

    for num, lst in enumerate(list_options):
        if lst == 'chosen':
            # style = None / CSS revert to initial; {display:initial}
            list_options[num] = None
        else:
            # CSS for hiding div
            list_options[num] = {'display': 'none'}

    return list_options


@app.callback(
    Output({"type": "new_input", "sim_id": ALL}, "disabled"),
    Output({"type": "collapse_row", "name": ALL}, "is_open"),
    Input({"type": "new_input", "sim_id": ALL}, "value"),
    State({"type": "new_input", "sim_id": ALL}, "disabled"),
    State({"type": "collapse_row", "name": ALL}, "is_open")
)
def cbf_gui_conditions(inp, state, state2):
    """
    This callback updates the settings portion of the GUI based on conditions defined in
    the styling.yaml-file.

    Currently to options are implemented: disabling ("gray out") and collapse ("hide")

    Note: Conditions are read from global variable "gui_conditions"

    Input: Triggerd by arbitrary input field change.

    Output: Two different outputs have to be given due to different location of action for "disable"
     and "collapse" options.


    """

    # Get state dictionaries ( id & property)
    disabled_states = dict(itertools.islice(ctx.states.items(), len(state)))
    collapse_open_states = dict(itertools.islice(ctx.states.items(), len(state), len(ctx.states)))

    # Differentiation between two possible options:
    # "disable" --> disable input fields
    # "collapse"--> collapse complete input row
    for action_type, conditions in gui_conditions.items():
        for targ_id, cond in conditions.items():
            trigger = False

            if action_type == "disable":
                for trig_id, trigg_data in cond.items():
                    trigger_state = ctx.inputs[f'{{"sim_id":"{trig_id}","type":"new_input"}}.value']
                    if trigger_state is None:
                        trigger_state = False
                    if trigger_state in trigg_data["values"]:
                        trigger = True

                disabled_states[f'{{"sim_id":"{targ_id}","type":"new_input"}}.disabled'] = trigger

            elif action_type == "collapse":
                for trig_id, trigg_data in cond.items():
                    trigger_state = ctx.inputs[f'{{"sim_id":"{trig_id}","type":"new_input"}}.value']
                    if trigger_state is None:
                        trigger_state = False
                    if trigger_state in trigg_data["values"]:
                        trigger = True

                collapse_open_states[f'{{"name":"{targ_id}","type":"collapse_row"}}.is_open'] = \
                    not trigger

            else:
                raise Exception("Undefined GUI action type. Check GUI definition.")

    return [v for _, v in disabled_states.items()], [v for _, v in collapse_open_states.items()]


if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=False)
