import yaml
import dash_bootstrap_components as dbc
from dash import dcc, html

# Width definitions
# --------------------------
# settings_widths defines first level widths for settings column.
# First level structure is ["Text", "Input Field(s)","Unit"]
settings_widths = [{"width": 5, "xl": 5}, {"width": 6, "xl": 6}, {"width": 1, "xl": 1}]
# inputfield_widths defines input field with INSIDE first level definition
inputfield_widths = {1: {"width": 6, "xl": 6},
                     2: {"width": 1, "xl": 6},
                     3: {"width": 1, "xl": 4},
                     4: {"width": 1, "xl": 3}}


def flatten_hierachical_simnames(definition_list: list) -> list:
    """

    :param definition_list: List with hierachical definitions of type
    [["...","...","..."],["...","...","..."],["...","...","..."]]
    :return:
    flattened definition list
    ["...-...-...", "...-...-...", ...]
    """
    flattened_simnames = []
    single_entry = False
    if not isinstance(definition_list[0], list):
        definition_list = [definition_list]
        single_entry = True

    for n, v in enumerate(definition_list):
        sim_name_flat = '-'.join(v)
        flattened_simnames.append(sim_name_flat)

    return flattened_simnames


def text_row_generic(texttype: str, text: str) -> dbc.Row:
    """
    Returns text row, either block heading or input field headings

    :param texttype:
    :param text:
    :return:
    """

    if texttype == "title":
        row = dbc.Row(dbc.Col(html.H5(text)))
    elif texttype == "column_headers":
        columns = []
        n_columns = 1 if not isinstance(text, list) else len(text)
        columns.append(dbc.Col("", **settings_widths[0]))
        columns.append(dbc.Col(dbc.Row([dbc.Col(text[n], **inputfield_widths[n_columns]) for n
                                        in range(n_columns)]), **settings_widths[1]))
        row = dbc.Row(columns)
    else:
        raise Exception(f"Undefined texttype {texttype}. Check GUI definition.")
    return row


def input_row_generic(name: str,
                      sim_name: list,
                      inputfield_type: str = "numeric",
                      disabled: list = None, **args) -> dbc.Row:
    """
    Creates dbc row with title and input fields.
    Example: Row title and 3 input fields -->    || Capex [%]   [...]  [...] [...] ||

    Structure: dbc.Row([dbc.Col(),dbc.Col(),...])


    :param name:
    :param sim_name:
    :param inputfield_type:
    :param disabled:        option to disable input field , default handling below
    :return:

    Args:
        inputfield_type:
    """

    # Check number of sim_names
    n_inputfields = 1 if not isinstance(sim_name[0], list) else len(sim_name)

    # Default non-disabled input fields
    if disabled is None:
        disabled = [False] * n_inputfields

    # First column: Label
    row_columns = [dbc.Col(dbc.Label(name), **settings_widths[0])]

    # # Add input-fields
    input_fields = []
    for n in range(n_inputfields):

        sim_name_flat = flatten_hierachical_simnames(sim_name)[n]

        if inputfield_type == "numeric":
            col = dbc.Col(dbc.Input(id={"type": "input", "sim_id": sim_name_flat},
                                    disabled=disabled[n],
                                    size="sm"),
                          **inputfield_widths[n_inputfields])
            input_fields.append(col)

        elif inputfield_type == "Dropdown":
            col = dbc.Col(
                dcc.Dropdown(args["values"], args["values"][0],
                             id={"type": "input", "sim_id": sim_name_flat}),
                **inputfield_widths[n_inputfields])
            input_fields.append(col)

        elif inputfield_type == "Checkbox":
            col = dbc.Col(
                dbc.Checkbox(id={"type": "input", "sim_id": sim_name_flat}),
                **inputfield_widths[n_inputfields])
            input_fields.append(col)
        else:
            raise Exception(f"Undefined inputfield_type {inputfield_type}. Check GUI definition.")

    input_field_col = dbc.Col(dbc.Row(input_fields), **settings_widths[1])
    row_columns.append(input_field_col)

    # Add unit
    col = dbc.Col(dbc.Label(args["unit"]),
                  **settings_widths[2])
    row_columns.append(col)
    return dbc.Row(row_columns)


def update_gui_conditions(combined_conditions: dict, conditions: list, add_target_ids=None,
                          target_row_ids=None) -> dict:
    """
    Input: list of condition-defining dictionaries of structure:
    [ {target_id:...,triggers: [[id:..., values= [...], action:...],[id:..., action:...],...]
    :param target_row_ids:
    :param add_target_ids:
    :param combined_conditions: To be updated condition dictionary
    :param conditions:

    :return:
    Restructured dict of conditions of structure:
    {{"action1":{target_id":{"trigger_id":{"values":[list of trigger values]},
                             "trigger_id2": ...}
                "target_id2": ...}
     {"action2": {....

    Args:
        target_row_ids:

    """

    conditions = [conditions] if isinstance(conditions, dict) else conditions
    for cond in conditions:

        # As conditions can adress different types of components, we differentiate between them
        # at highes level. Cleaner solution could be: Highest-level differentiation is not action,
        # but target object as ("field", "row", "block")
        c_action = cond["action"]
        trigger_id = flatten_hierachical_simnames(cond["trigger_id"])[0]

        if c_action == "disable":
            # If add_target_ids are given, these come from conditions inside row definition and need
            # to be added. It is expected, that for each id one conditions was given, otherwise
            # raise Exception
            if add_target_ids:
                # ... function was called from row definition and target_ids needs to added.
                if len(add_target_ids) == len(conditions):
                    for i, _ in enumerate(conditions):
                        conditions[i]["target_ids"] = [add_target_ids[i]]
                else:
                    raise Exception(
                        f"Attention! Unmatching number of sim names and given conditions for gui"
                        f" definition :{add_target_ids}")

            targ_ids = flatten_hierachical_simnames(cond["target_ids"])
            for targ_id in targ_ids:
                # ... check if target_id is defined in combined conditions, otherwise do it
                if targ_id not in combined_conditions["disable"]:
                    combined_conditions["disable"][targ_id] = {}
                # Add entry
                combined_conditions["disable"][targ_id][trigger_id] = {
                    "values": cond["trigger_cond"]}

        elif c_action == "collapse":
            targ_ids = [target_row_ids] if isinstance(target_row_ids, str) else target_row_ids
            for targ_id in targ_ids:
                if targ_id not in combined_conditions["collapse"]:
                    combined_conditions["collapse"][targ_id] = {}
                # Add entry
                combined_conditions["collapse"][targ_id][trigger_id] = {
                    "values": cond["trigger_cond"]}
        else:
            raise Exception(f"Undefined condition given: {c_action}. Check GUI definition.")

    return combined_conditions


def create_gui_from_def_structure(gui_definition_dict: dict) -> (dbc.Row, list):
    """

    :return
    - dbc.Row GUI definition
    - List of condition-dicts of type
        [ {target_id:...,triggers: [[id:..., values= [...], action:...],[id:..., action:...],...]
    """
    combined_conditions = {"collapse": {}, "disable": {}}
    tabs = []
    for tab_n, tab_v in gui_definition_dict.items():  # Create tab

        tab_title = tab_v["title"]
        tab_content = []
        for block_n, block_v in {k: v for k, v in tab_v.items() if
                                 k[:5] == "block"}.items():  # Create block
            # Create input block...
            block_title = block_v["title"] if "title" in block_v else None
            column_headers = block_v["column_headers"] if "column_headers" in block_v else None
            column_headers2 = block_v["column_headers2"] if "column_headers2" in block_v else None
            block_content = []
            if block_title:
                block_content.append(text_row_generic(texttype="title", text=block_title))
            if column_headers:
                block_content.append(text_row_generic(texttype="column_headers",
                                                      text=column_headers))
            if column_headers2:
                block_content.append(text_row_generic(texttype="column_headers",
                                                      text=column_headers2))

            for row_n, row_v in {k: v for k, v in block_v.items() if k[:3] == "row"}.items():
                # Note: Implementation below is not differentiating, gives dbc.Collapse Element
                # to each row with internal id.
                # ToDo We could update logic to only provide dbc.Collapse if required.
                row = input_row_generic(**row_v)
                internal_row_name = f"{tab_n}-{block_n}-{row_n}"
                row = dbc.Collapse(row,
                                   id={"type": "collapse_row",
                                       "name": f"{tab_n}-{block_n}-{row_n}"},
                                   is_open=True)
                block_content.append(row)

                # Handling of different conditions for visualization of GUI elements
                if "condition_behaviour" in row_v:
                    combined_conditions = update_gui_conditions(
                        combined_conditions=combined_conditions,
                        conditions=row_v["condition_behaviour"],
                        add_target_ids=row_v["sim_name"],
                        target_row_ids=internal_row_name)

            block_content.append(html.Br())
            tab_content.extend(block_content)

        # Read block-level  conditions:
        for _, blockcond_v in {k: v for k, v in tab_v.items() if
                               k[:19] == "condition_behaviour"}.items():  # Create block
            combined_conditions = update_gui_conditions(combined_conditions=combined_conditions,
                                                        conditions=blockcond_v)

        tab = dbc.Tab(label=tab_title, children=tab_content)
        tabs.append(tab)

    gui = dbc.Tabs([t for t in tabs])
    return gui, combined_conditions


def create_gui_from_definition_file(def_file: str):
    if def_file[-4:] == "yaml":
        with open(def_file, 'r') as stream:
            data_loaded = yaml.safe_load(stream)

    gui, gui_conditions = create_gui_from_def_structure(data_loaded)

    return gui, gui_conditions


if __name__ == "__main__":
    ...
