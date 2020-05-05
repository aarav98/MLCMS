import sys
import system as model
import json


def initialize_system(file_name):
    """
    Reads the scenario file and initializes the system with pro
    :param file_name:
    :return:
    """
    with open(file_name) as scenario:
        data = json.load(scenario)
    rows = data['rows']
    cols = data['cols']
    system = model.System(cols, rows)
    for col, row in data['pedestrians']:
        system.add_pedestrian((col, row))

    for col, row in data['obstacles']:
        system.add_obstacle((col, row))

    col, row = data['target']
    target = system.add_target((col, row))

    #model.evaluate_cell_distance(system, target)
    return system

system=initialize_system('Scenarios/scenario_task2.json')
print("success!")

system.calc_fmm()
#system.calc_fmm_path()
