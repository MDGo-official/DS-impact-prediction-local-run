import json
import os
#import bokeh.plotting
#import bokeh.io


class IO:

    @classmethod
    def read_config(cls,base_folder,package_name):
        with open(os.path.join(base_folder,'config',package_name+'_config.json'),'r') as fin:
            conf=json.load(fin)

        return conf

    '''
    @classmethod
    def dump_plt(cls, base_folder, package_name, name, figure_data):
        """
        :param base_folder: basefolder
        :param package_name: Calibration, Crash, Damages, Medical
        :param name: name without extension
        :param figure_data: object from plt or df.plot().get_figure()
        :return:
        """
        try:
            path = os.path.join(base_folder, "GNG_data", package_name, package_name+" - "+name + ".png")
            figure_data.savefig(path)
        except OSError as e:
            return "Failed to make plt plot. Error: {}".format(e)

    @classmethod
    def dump_bokeh(cls, base_folder, package_name, name, figure_data):
        """
        :param base_folder: basefolder
        :param package_name: Calibration, Crash, Damages, Medical
        :param name: name without extension
        :param figure_data: bokeh figure object
        :return:
        """
        try:
            path = os.path.join(base_folder, "GNG_data", package_name, package_name+" - "+name + ".html")
            bokeh.plotting.output_file(path)
            bokeh.io.save(figure_data)
        except OSError as e:
            return "Failed to make Bokeh plot. Error: {}".format(e)
'''

    @classmethod
    def dump_json(cls,  base_folder, package_name, name, json_data):
        """
        :param base_folder: basefolder
        :param package_name: Calibration, Crash, Damages, Medical
        :param name: name without extension
        :param json_data:
        :return:
        """
        path = os.path.join(base_folder, "GNG_data", package_name, package_name+" - "+name + ".json")
        try:
            with open(path, 'w') as fout:
                json.dump(json_data, fout, indent=4)
        except OSError as e:
            return "Failed to write json. Error: {}".format(e)

    @classmethod
    def dump_txt(cls, base_folder, package_name, name, text):
        """
        :param base_folder: basefolder
        :param package_name: Calibration, Crash, Damages, Medical
        :param name: name without extension
        :param text:
        :return:
        """
        path = os.path.join(base_folder, "GNG_data", package_name, package_name+" - "+name + ".txt")
        try:
            with open(path, 'w') as fout:
                fout.write(text)
        except OSError as e:
            return 'Failed to write text. Error: {}'.format(e)

    @classmethod
    def dump_csv(cls,  base_folder, package_name, name, df_data):
        """
        :param base_folder: basefolder
        :param package_name: Calibration, Crash, Damages, Medical
        :param name: name without extension
        :param df_data:
        :return:
        """
        path = os.path.join(base_folder, "GNG_data", package_name, name + ".csv")
        try:
            df_data.to_csv(path, index=False)
        except OSError as e:
            return "Failed to write json. Error: {}".format(e)
