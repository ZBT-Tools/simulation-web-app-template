from functools import wraps
import data_transfer
import base64
import io
import json
import pickle
import jsonpickle
import collections
import ast
from itertools import product
from glom import glom
import pandas as pd
import numpy as np
from . import simulation_api as sim_api
from . import dash_layout as dl


def run_simulation(input_table: pd.DataFrame, return_unsuccessful=True) \
        -> (pd.DataFrame, bool):
    """
    - Run input_table rows, catch exceptions of single calculations
      https://stackoverflow.com/questions/22847304/exception-handling-in-pandas-apply-function
    - Append result columns to input_table
    - Return DataFrame
    """

    def func(settings):
        try:
            return sim_api.run_external_simulation(settings)
        except Exception as E:
            return repr(E)

    result_table = input_table["settings"].progress_apply(func)
    # result_table = input_table["settings"].map(func)
    # result_table = input_table["settings"].parallel_apply(func)
    # result_table = input_table["settings"].apply_parallel(func, num_processes=4)

    input_table["global_data"] = result_table.apply(
        lambda x: x[0][0] if (isinstance(x, tuple)) else None)
    input_table["local_data"] = result_table.apply(
        lambda x: x[1][0] if (isinstance(x, tuple)) else None)
    input_table["successful_run"] = result_table.apply(
        lambda x: True if (isinstance(x[0], list)) else False)

    all_successfull = True if input_table["successful_run"].all() else False

    if not return_unsuccessful:
        input_table = input_table.loc[input_table["successful_run"], :]

    return input_table, all_successfull


def convert_to_storage_format(data):
    """
    https://github.com/jsonpickle/jsonpickle, as json.dumps can only handle
    simple variables, no objects, DataFrames..
    Info: Eigentlich sollte jsonpickle reichen, um dict mit Klassenobjekten,
    in denen DataFrames sind, zu speichern, es gibt jedoch Fehlermeldungen.
    Daher wird Datenstruktur vorher in pickle (Binärformat)
    gespeichert und dieser anschließend in json konvertiert.
    (Konvertierung in json ist notwendig für lokalen dcc storage)
    """
    data = pickle.dumps(data)
    data = jsonpickle.dumps(data)
    return data


def read_storage_data_format(data):
    # Read data from storage
    data = jsonpickle.loads(data)
    data = pickle.loads(data)
    return data


def interpolate_1d(array, add_edge_points=False):
    """
    Linear interpolation in between the given array data. If
    add_edge_points is True, the neighbouring value from the settings array is
    used at the edges and the returned array will larger than the settings array.
    """
    array = np.asarray(array)
    interpolated = (array[:-1] + array[1:]) * .5
    if add_edge_points:
        first = np.asarray([array[0]])
        last = np.asarray([array[-1]])
        return np.concatenate((first, interpolated, last), axis=0)
    else:
        return interpolated


def convert_gui_state_to_sim_dict(gui_state: list) -> dict:
    """
    Input
    GUI input field list (e.g. from ctx.states_list[0])

    Return
    Dictionary in format of simulation (including lists)

    """
    gui_ids = [el['id']['sim_id'] for el in gui_state]
    gui_vals = [el['id']['value'] if 'value' in el['id'] else None for el in gui_state]

    # Combine values to lists for suffix "-0", "-1","-n", identifying belonging togehter values
    gui_dict = {}
    for gui_id, gui_val in zip(gui_ids, gui_vals):
        # Check 'multi-input'
        if gui_id[-1].isdigit() and gui_id[-2] == "-":
            # Check if name is available
            sim_name = gui_id[:-2]
            if sim_name in gui_dict:
                # Add value to list
                gui_dict[sim_name].append(gui_val)
            else:
                # create entry
                gui_dict[sim_name] = [gui_val]
        else:
            sim_name = gui_id
            gui_dict[sim_name] = gui_val

    return gui_dict

def convert_sim_dict_to_state_value_list(sim_dict: dict, state_list: list) -> list:
    """
    Undo combination of values to lists for suffix "-0", "-1","-n",
    identifying togehter belonging values
    return values in list, order defined by state_list
    """

    gui_dict = {}
    for k, v in sim_dict.items():
        if isinstance(v, list):
            for n, le in enumerate(v):
                gui_dict[f"{k}-{n}"] = le
        else:
            gui_dict[k] = v

    gui_id_list = [el['id']['sim_id'] for el in state_list]
    value_list = [gui_dict[le] for le in gui_id_list]

    return value_list

def create_settings(df_data: pd.DataFrame, settings,
                    input_cols=None) -> pd.DataFrame:
    # Create settings dictionary
    # If "input_cols" are given, only those will be used from "df_data".
    # Usecase: df_data can contain additional columns as study information
    # that needs to be excluded from settings dict
    # -----------------------------------------------------------------------
    # Create object columns
    df_temp = pd.DataFrame(columns=["input_data", "settings"])
    df_temp['input_data'] = df_temp['input_data'].astype(object)
    df_temp['settings'] = df_temp['input_data'].astype(object)

    if input_cols is not None:
        df_data_red = df_data.loc[:, input_cols]
    else:
        df_data_red = df_data

    # Create input data dictionary (legacy)
    df_temp['input_data'] = df_data_red.apply(
        lambda row: {i: {'sim_name': i.split('-'), 'value': v}
                     for i, v in zip(row.index, row.values)}, axis=1)

    # ToDO: continue here FKL
    df_temp['settings'] = df_temp['input_data'].apply(
        lambda x: data_transfer.dict_transfer(x, settings)[0])
    data = df_data.join(df_temp)

    return data


def unstringify(val):
    """
    Used to change any str value created by DBC.Input once initialised due to
    not defining the component as type Number.
    """
    if isinstance(val, str):
        if '.' in val:
            try:
                yield float(val)
            except (ValueError, NameError):
                yield val
        else:
            try:
                yield int(val)
            except (ValueError, NameError):
                yield val
    elif isinstance(val, list):
        try:
            yield list((float(v) for v in val))
        except ValueError:
            yield list((v for v in val))
    else:
        yield val


# def multi_inputs(dicts):
#     """
#     Deal with components that have multiple values and multiple IDs from
#     id-value dicts
#     (can be found inside def process_inputs; dicts pre-processed inside the
#     function)
#     """
#     dict_list = {}
#     for k, v in dicts.items():
#         if k[-1:].isnumeric() is False:
#             dict_list.update({k: v})
#         else:
#             if k[:-2] not in dict_list:
#                 dict_list.update({k[:-2]: v})
#             elif k[:-2] in dict_list:
#                 if not isinstance(dict_list[k[:-2]], list):
#                     new_list = [dict_list[k[:-2]]]
#                 else:
#                     new_list = dict_list[k[:-2]]
#                 new_list.append(v)
#                 dict_list.update({k[:-2]: new_list})
#     return dict_list


def parse_contents(
        contents: str, filename: str, dtype: (dict, pd.DataFrame) = dict) \
        -> (dict, pd.DataFrame):
    """
    Parse contents from different file types loaded via dash upload component
    that encodes as base64 string.
    [https://dash.plotly.com/dash-core-components/upload]
    Returns data either as dictionary or Pandas DataFrame, depending on the
    'data_type' setting

    :param contents: contents is a base64 encoded string that contains the
        files contents, no matter what type of file: text files, images,
        .zip files, Excel spreadsheets, etc.
    :param filename: File name string
    :param dtype: type specifier for the returned data type
    :return: Converted data
    """
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    # Assume that the user uploaded a CSV file
    if 'json' in filename:
        return json.load(io.StringIO(decoded.decode('utf-8')))
    else:
        if 'csv' in filename:
            data = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            data = pd.read_excel(io.BytesIO(decoded))
        else:
            raise TypeError('Only json, csv, or xls file types can be read at '
                            'the moment')
        if dtype is pd.DataFrame:
            return data
        elif dtype is dict:
            return data.to_dict()
        else:
            raise TypeError('Data can only be returned as Pandas DataFrame'
                            ' or Python Dictionary')


def settings_to_dash_gui_format(settings: dict) -> (dict, list):
    """
    Convert settings from the hierarchical simulation input dictionary to
    a dictionary for the gui input combining all hierarchical keys to a single
    id key string and the entry value.
    Example:
    input: settings_dict = {'stack': {'cathode': {'channel': {'length': 0.5}}}}
    return: gui_dict = {'stack-cathode-channel-length': 0.5}
    """
    #name_lists = [ids['id'].split('-') if ids['id'][-1:].isnumeric() is False
    #              else ids['id'][:-2].split('-') for ids in dl.ID_LIST]
    error_list = []
    gui_dict = {}
    for k,v in settings.items():

        name_id = '-'.join(n)
        try:
            gui_dict.update({name_id: glom(settings, '.'.join(n))})
        except Exception as e:
            # print(e)
            error_list.append(name_id)
    return gui_dict, error_list


def update_gui_settings_dict(new_settings_dict: dict, old_settings_dict: dict,
                               mode='update') -> dict:
    """
    ToDO: keep old_vals and ids in one variable, fail safe!

    Input
    new_settings_dict: dict:    Dictionary with program setting data, example:
                                {'stack-cell_number':10,
                                'anode-bpp-electrical_conductivity':[60000,60000]}
    old_settings_dict: dict:    to be updated settings dictionary (same format
    mode:                       if "update" only keys which are already in old_settings_dict
                                will be updated.
                                Potential other implementation "extend" could add new keys to
                                old_settings_dict


    Return
    Updated settings dictionary
    """
    if mode == "update":
        # Reduce new_settings_dict to available keys in old_settings_dict
        shared_keys = new_settings_dict.keys() & old_settings_dict.keys()
        update_dict = {k: new_settings_dict[k] for k in shared_keys}
        old_settings_dict.update(update_dict)
        return old_settings_dict
    else:
        raise TypeError('Unknown mode!')


def check_ifbool(val):
    """
    Used for dcc.Checklist components when receiving value from its
    tkinter.CheckButton counterparts
    """
    if isinstance(val, bool):
        if val is True:
            return [1]
        else:
            return []
    else:
        return val


def convert_gui_settings_to_DataFrame(gui_settings_dict:dict):
    """
    ToDO
    """

    df_data = pd.DataFrame()
    input_data = {}
    for k, v in gui_settings_dict.items():
        # Info: pd.DataFrame.at instead of .loc, as .at can put lists into
        # df cell.
        # .loc can be used for passing values to more than one cell,
        # that's why passing lists is not possible.
        # Column must be of type object to accept list-objects
        # https://stackoverflow.com/questions/26483254/python-pandas-insert-list-into-a-cell
        df_data.at["nominal", k] = None
        df_data[k] = df_data[k].astype(object)
        df_data.at["nominal", k] = v
    return df_data


def variation_parameter(df_input: pd.DataFrame, table_input,
                        keep_nominal=False, mode="single") -> pd.DataFrame:
    """
    Function to create parameter sets.
    - variation of single parameter - ok
    - (single) variation of multiple parameters - ok
    - combined variation of multiple parameters
        - full factorial - ok

    Important: Change casting_func to int(),float(),... accordingly!
    """

    # Define parameter sets
    # -----------------------

    var_par_names = \
        [le["Parameter"] for le in table_input
         if le["Variation Type"] is not None]

    # Comment on ast...: ast converts string savely into int,float, list,...
    # It is required as input in DataTable is unspecified and need to be
    # cast appropriately.
    # On the other-hand after uploading table, values can be numeric,
    # which can cause Error.
    # Solution: Cast input always to string (required for uploaded data) and
    # then eval with ast
    var_par_values = \
        [ast.literal_eval(str(le["Values"])) for le in table_input
         if le["Variation Type"] is not None]
    var_par_variationtype = \
        [le["Variation Type"] for le in table_input
         if le["Variation Type"] is not None]
    var_par_cast = []

    # var_par_cast = [ast.literal_eval(str(le["Variation Type"]))
    # for le in table_input if le["Variation Type"] is not None]

    for le in var_par_values:
        le_type = type(le)
        if le_type == tuple:
            le_type = type(le[0])
        var_par_cast.append(le_type)

    # Caluclation of values for percent definitions
    processed_var_par_values = []
    for name, vls, vartype \
            in zip(var_par_names,
                   var_par_values, var_par_variationtype):
        nom = df_input.loc["nominal", name]
        if vartype == "Percent (+/-)":
            perc = vls
            if isinstance(nom, list):
                # nomval = [cst(v) for v in nom]
                processed_var_par_values.append(
                    [[v * (1 - perc / 100) for v in nom],
                     [v * (1 + perc / 100) for v in nom]])
            else:
                # nomval = cst(nom)
                processed_var_par_values.append([nom * (1 - perc / 100),
                                                 nom * (1 + perc / 100)])

        else:
            processed_var_par_values.append(list(vls))

    var_parameter = \
        {name: {"values": val} for name, val in
         zip(var_par_names, processed_var_par_values)}

    # Add informational column "variation_parameter"
    clms = list(df_input.columns)
    clms.extend(["variation_parameter"])
    data = pd.DataFrame(columns=clms)

    if mode == "single":  #
        # ... vary one variation_parameter, all other parameter nominal
        # (from GUI)
        for parname, attr in var_parameter.items():
            for val in attr["values"]:
                inp = df_input.copy()
                inp.loc["nominal", parname] = val
                inp.loc["nominal", "variation_parameter"] = parname
                data = pd.concat([data, inp], ignore_index=True)

    elif mode == "full":
        # see https://docs.python.org/3/library/itertools.html

        parameter_names = [key for key, val in var_parameter.items()]
        parameter_names_string = ",".join(parameter_names)
        parameter_values = [val["values"] for key, val in var_parameter.items()]
        parameter_combinations = list(product(*parameter_values))

        for combination in parameter_combinations:
            inp = df_input.copy()
            inp.loc["nominal", "variation_parameter"] = parameter_names_string
            for par, val in zip(parameter_names,
                                combination):
                inp.at["nominal", par] = val
            data = pd.concat([data, inp], ignore_index=True)

    if keep_nominal:
        data = pd.concat([data, df_input])

    return data
