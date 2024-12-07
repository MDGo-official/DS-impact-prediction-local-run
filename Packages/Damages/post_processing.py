import numpy as np
import collections
import copy
from Utils import LogLevel, DSLogger
import os

class PostProcessing:
    def __init__(self, result, config, mechanism, **kwargs):
        self.logger = DSLogger("Damages_log")
        self.logger.PrintLog(LogLevel.Info, f"Initialization of post-processing")
        self.original_result = copy.deepcopy(result)
        self.fixed_result = copy.deepcopy(result)
        self.mechanism = mechanism
        self.config = copy.deepcopy(config)
        self.config["post_process_dict"] = {eval(k): v for k, v in config["post_process_dict"].items()}
        self.theta = kwargs["theta"] if "theta" in kwargs else None
        self.DV = kwargs["DV"] if "DV" in kwargs else None
        self.car_type = kwargs["car_type"] if "car_type" in kwargs else None
        self.post_process_dict = self.config["post_process_dict"][self.get_angle_interval()]
        self.logger.PrintLog(LogLevel.Info, f"theta: {self.theta}, post-process dict: {self.post_process_dict},"
                                            f" initial_mechanism: {self.mechanism}")
        self.logger.PrintLog(LogLevel.Info, f"original damage cells: {self.original_result}")
        self.possible_damage_cells = self.config["mechanism_dict"][self.mechanism]
        self.possible_damage_cells = [str(i) for i in self.possible_damage_cells]

    def get_angle_interval(self):
        for k in self.config["post_process_dict"].keys():
            if k[0] < k[1]:
                if k[0] < self.theta <= k[1]:
                    return k
            elif k[0] < self.theta or self.theta <= k[1]:
                return k

    def get_possible_damage_cells(self):
        num_cells_per_mechanism = {k: 0 for k in self.post_process_dict['mechanisms']}
        for ind in range(3):
            for k in num_cells_per_mechanism.keys():
                if k in ["Frontal", "Rear"]:
                    num_cells_per_mechanism[k] = len([cell for cell in self.fixed_result if cell.split("_")[2] ==
                                                      str(self.config["mechanism_dict"][k][ind])])
                else:
                    num_cells_per_mechanism[k] = len([cell for cell in self.fixed_result if cell.split("_")[1] ==
                                                      str(self.config["mechanism_dict"][k][ind])])
            if len(set(num_cells_per_mechanism.values())) == 2:
                self.mechanism = max(num_cells_per_mechanism, key=num_cells_per_mechanism.get)
                self.possible_damage_cells = self.config["mechanism_dict"][self.mechanism]
                self.possible_damage_cells = [str(i) for i in self.possible_damage_cells]
                break

    def get_final_results(self):
        removed = list(self.original_result - self.fixed_result)
        added = list(self.fixed_result - self.original_result)
        final_result = {"final": list(self.fixed_result), "added": added, "removed": removed}
        return final_result

    def fix_corner_cells(self, add_cells=False):
        if len(self.fixed_result) > 0:
            temp_result = self.fixed_result.copy()
            for cell in temp_result:
                if "A_1_" in cell or "F_1_" in cell:
                    if self.mechanism == "Frontal":
                        new_cell = cell.replace("_1_", "_2_")
                    elif self.mechanism == "SideLeft":
                        new_cell = cell.replace("F_1_", "F_2_")
                    elif self.mechanism == "SideRight":
                        new_cell = cell.replace("A_1_", "A_2_")
                    else:
                        continue
                    if add_cells:
                        self.fixed_result.add(new_cell)
                    else:
                        self.fixed_result.discard(cell)

    def fix_edge_cells(self):
        if len(self.fixed_result) > 0:
            for cell in self.post_process_dict["edge"]:
                if ("Cell_" + cell + "_Low") in self.fixed_result:
                    if "A_" in cell and ("Cell_" + cell.replace("A_", "B_") + "_Low") not in self.fixed_result:
                        if "_2" in cell:
                            temp = set([cell for cell in self.fixed_result if cell.split("_")[1] == "A" and
                                        int(cell.split('_')[2]) >= 2])
                        else:
                            temp = set([cell for cell in self.fixed_result if cell.split("_")[1] == "A" and
                                        int(cell.split('_')[2]) <= 12])
                        self.fixed_result = self.fixed_result - temp
                    elif "F_" in cell and ("Cell_" + cell.replace("F_", "E_") + "_Low") not in self.fixed_result:
                        if "_2" in cell:
                            temp = set([cell for cell in self.fixed_result if cell.split("_")[1] == "F" and
                                        int(cell.split('_')[2]) >= 2])
                        else:
                            temp = set([cell for cell in self.fixed_result if cell.split("_")[1] == "F" and
                                        int(cell.split('_')[2]) <= 12])
                        self.fixed_result = self.fixed_result - temp

    def fix_cells_by_mechanism(self):
        if self.mechanism in ["Frontal", "Rear"]:
            self.fixed_result = set(
                [cell for cell in self.fixed_result if cell.split("_")[2] in self.possible_damage_cells])
        elif self.mechanism in ["SideLeft", "SideRight"]:
            self.fixed_result = set(
                [cell for cell in self.fixed_result if cell.split("_")[1] in self.possible_damage_cells])

    def fill_gap(self):
        new_result = set()
        if self.mechanism in ["Rear", "Frontal"]:
            elem = ["A", "B", "C", "D", "E", "F"]
            for i, line in enumerate(self.possible_damage_cells):
                line_cells = set([cell for cell in self.fixed_result if cell.split("_")[2] == line])
                line_cells = self.fixed_by_vertical(i, line_cells)
                for level in ["High", "Low"]:
                    level_cells = set([cell.split("_")[1] for cell in line_cells if level in cell])
                    if 0 < len(level_cells) < len(elem):
                        empty_elem = set(elem) - level_cells
                        for c in empty_elem:
                            ind = elem.index(c)
                            if 0 < ind < 5 and (elem[ind - 1] in level_cells and elem[ind + 1] in level_cells):
                                level_cells.add(c)
                        level_cells = set([f"Cell_{c}_{line}_{level}" for c in level_cells])
                        line_cells.update(level_cells)
                new_result.update(line_cells)
        elif self.mechanism in ["SideLeft", "SideRight"]:
            elem = [str(i) for i in range(1, 14)]
            for i, line in enumerate(self.possible_damage_cells):
                line_cells = set([cell for cell in self.fixed_result if cell.split("_")[1] == line])
                line_cells = self.fixed_by_vertical(i, line_cells)
                for level in ["High", "Low"]:
                    level_cells = set([cell.split("_")[2] for cell in line_cells if level in cell])
                    if 0 < len(level_cells) < len(elem):
                        empty_elem = set(elem) - level_cells
                        for c in empty_elem:
                            ind = elem.index(c)
                            if 0 < ind < 12 and (elem[ind - 1] in level_cells and elem[ind + 1] in level_cells):
                                level_cells.add(c)
                        level_cells = set([f"Cell_{line}_{c}_{level}" for c in level_cells])
                        line_cells.update(level_cells)
                new_result.update(line_cells)
        return new_result

    def del_cells(self):
        new_result = set()
        if self.mechanism in ["Rear", "Frontal"]:
            elem = ["A", "B", "C", "D", "E", "F"]
            for i, line in enumerate(self.possible_damage_cells):
                line_cells = set([cell for cell in self.fixed_result if cell.split("_")[2] == line])
                for level in ["High", "Low"]:
                    level_cells = set([cell.split("_")[1] for cell in line_cells if level in cell])
                    if i == 0:
                        if 1 < len(level_cells) < len(elem):
                            for c in level_cells:
                                ind = elem.index(c)
                                check_ind = [ind + i for i in [-1, +1] if 0 <= ind + i < len(elem)]
                                if not any([elem[i] in level_cells for i in check_ind]):
                                    line_cells.discard(f"Cell_{c}_{line}_{level}")
                    else:
                        for c in level_cells:
                            if f"Cell_{c}_{self.possible_damage_cells[i - 1]}_{level}" not in new_result:
                                line_cells.discard(f"Cell_{c}_{line}_{level}")
                new_result.update(line_cells)
        elif self.mechanism in ["SideLeft", "SideRight"]:
            elem = [str(i) for i in range(1, 14)]
            for i, line in enumerate(self.possible_damage_cells):
                line_cells = set([cell for cell in self.fixed_result if cell.split("_")[1] == line])
                for level in ["High", "Low"]:
                    level_cells = set([cell.split("_")[2] for cell in line_cells if level in cell])
                    if i == 0:
                        if 1 < len(level_cells) < len(elem):
                            for c in level_cells:
                                ind = elem.index(c)
                                check_ind = [ind + i for i in [-1, +1] if 0 <= ind + i < len(elem)]
                                if not any([elem[i] in level_cells for i in check_ind]):
                                    line_cells.discard(f"Cell_{line}_{c}_{level}")
                    else:
                        for c in level_cells:
                            if f"Cell_{self.possible_damage_cells[i - 1]}_{c}_{level}" not in new_result:
                                line_cells.discard(f"Cell_{line}_{c}_{level}")
                new_result.update(line_cells)
        return new_result

    def fixed_by_vertical(self, i, line_cells):
        new_line_cell = copy.deepcopy(line_cells)
        if i > 0:
            for cell in line_cells:
                if self.mechanism in ["Frontal", "Rear"] and ("_A_" in cell or "_F_" in cell):
                    if "High" in cell:
                        if cell.replace("High", "Low") not in line_cells:
                            new_line_cell.discard(cell)
                elif "Side" in self.mechanism and ("_1_" in cell or "_13_" in cell):
                    if "High" in cell:
                        if cell.replace("High", "Low") not in line_cells:
                            new_line_cell.discard(cell)
                else:
                    if "High" in cell:
                        new_line_cell.add(cell.replace("High", "Low"))
                    else:
                        new_line_cell.add(cell.replace("Low", "High"))
        else:
            for cell in line_cells:
                if "High" in cell:
                    if cell.replace("High", "Low") not in line_cells:
                        new_line_cell.discard(cell)
        return new_line_cell

    def run(self):
        if len(self.original_result) == 0:
            return self.get_final_results()
        self.get_possible_damage_cells()
        self.logger.PrintLog(LogLevel.Info, f"fixed mechanism {self.mechanism}")
        self.fix_cells_by_mechanism()
        # self.fill_gap()
        self.fix_corner_cells(add_cells=True)
        self.fixed_result = self.fill_gap()
        self.fixed_result = self.del_cells()
        self.fix_corner_cells(add_cells=False)
        self.fix_edge_cells()
        return self.get_final_results()
