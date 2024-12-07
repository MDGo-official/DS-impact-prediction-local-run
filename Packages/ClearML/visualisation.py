import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatch


class Visualisation:

    @classmethod
    def plot_damage_cells(cls, result):
        '''
        Function to plot damages
        result - list of damage cells
        '''

        W = {"F": (0, 2), "E": (2, 4), "D": (4, 10), "C": (10, 16), 'B': (16, 18), "A": (18, 20)}
        L = {1: (0, 3), 2: (3, 6), 3: (6, 12), 4: (12, 17), 5: (17, 20), 6: (20, 28),
             7: (28, 31), 8: (31, 38), 9: (38, 41), 10: (41, 45), 11: (45, 51), 12: (51, 57), 13: (57, 60)}
        fig_main, ax_main = plt.subplots(2, figsize=(18, 18))
        for j, level in enumerate(['High', "Low"]):
            data = ["_".join(cell.split("_")[:-1]) for cell in result if level in cell]
            Cells = dict()
            for w, valW in W.items():
                for l, valL in L.items():
                    name = w + "_" + str(l)
                    #         corner = (valL[0], valW[0])
                    Cells[name] = [[valL[0], valW[0]], [valL[1], valW[0]], [valL[1], valW[1]], [valL[0], valW[1]]]

            ax = ax_main[j]
            for r in Cells.keys():
                cell = "Cell_" + r
                if cell in data:
                    ax.add_patch(mpatch.Polygon(Cells[r], closed=True, fill=True, ec="k", color='b'))
                else:
                    ax.add_patch(mpatch.Polygon(Cells[r], closed=True, fill=True, ec="k", color='w'))
            for k, v in W.items():
                if j == 1:
                    fig_main.text(6.5 / 60, 0.12 + (10.5 + np.mean(v) / 2.1) / 26.3, k, fontsize=16, color="r")
                else:
                    fig_main.text(6.5 / 60, 0.1 + (np.mean(v) / 2.1) / 26.3, k, fontsize=16, color="r")
            for k, v in L.items():
                if j == 1:
                    fig_main.text(0.12 + np.mean(v) / 77.2, 13.5 / 26.3, k, fontsize=16, color="r")
                else:
                    fig_main.text(0.12 + np.mean(v) / 77.2, 2.5 / 26.3, k, fontsize=16, color="r")
            ax.set_xlim((0, 60))
            ax.set_ylim((0, 20))
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title("Damage cells on level {}".format(level), fontsize=16)
        return fig_main

    @classmethod
    def df_to_plot_plotly(cls, df, time_axis=True):
        pd.options.plotting.backend = "plotly"
        if time_axis:
            fig = df.plot(x=df.columns[0], y=df.columns[1:])
        else:
            fig = df.plot()
        return fig

    @classmethod
    def df_to_plot_matplotlib(cls, df, time_axis=True):
        pd.options.plotting.backend = "matplotlib"
        if time_axis:
            fig = df.plot(x=df.columns[0], y=df.columns[1:], figsize=(8, 6), grid=True).get_figure()
        else:
            fig = df.plot(figsize=(8, 6), grid=True).get_figure()
        return fig

