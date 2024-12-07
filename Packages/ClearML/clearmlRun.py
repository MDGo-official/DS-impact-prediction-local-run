import sys
import traceback
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from clearml import Task
import time
from Utils import *
from ClearML import ClearmlUtility
from ClearML import Visualisation
from SignalProcessing import SignalProcessing as sp
import traceback
import datetime


class RunEvent:
    def __init__(self, basefolder, event_obj):
        self.logger = DSLogger("ClearML_log")
        self.logger.PrintLog(LogLevel.Info, "ClearML: module initialization")
        self.logger.PrintLog(LogLevel.Info, f"ClearML: {event_obj.keys()}")
        self.clearml_config = IO.read_config(basefolder, 'clearml')
        self.sigFs = self.clearml_config["sample_rate"]
        if not isinstance(event_obj, dict):
            self.logger.PrintLog(LogLevel.Error, "event_obj should be dict")
            sys.exit(1)
        self.event_obj = event_obj

    def getMetaData(self):
        meta = self.event_obj["Event"]
        self.event_id = meta["_id"]
        self.eventTime = str(meta['EventTime'])
        self.receivingTime = str(meta["ReceivingTime"])
        self.offset = meta["ExtraProperties"]["Offset"]
        self.AllocatedTo = meta["ExtraProperties"]['AllocatedTo']
        self.coordinates = meta['EventLocation']['coordinates']
        self.SerialNumber = meta["ExtraProperties"]["SerialNumber"]
        self.DeviceID = meta["DeviceID"]


    def connect_to_task(self):
        project_name = self.AllocatedTo + " " + "Event"
        prj_names = [i.name for i in Task.get_projects()]
        if project_name not in prj_names:
            task = ClearmlUtility.task_init(project_name=project_name, task_name=self.event_id)
        else:
            task = ClearmlUtility.get_task(project_name=project_name, task_name=self.event_id, reset=False)
            if task is None:
                task = ClearmlUtility.task_init(project_name=project_name, task_name=self.event_id)
        self.task = task
        self.clLogger = self.task.get_logger()
        if 'General/eventTime' not in self.task.get_parameters():
            ClearmlUtility.add_object_task(task=self.task, object={"eventTime": self.eventTime, "receivingTime": self.
                                           receivingTime})

    def reportLocation(self):
        url = f"https://www.google.com/maps/search/?api=1&query={self.coordinates[1]} {self.coordinates[0]}"
        ClearmlUtility.report_html_url(title="maps", url=url)

    def getRawData(self):
        _, self.rawData_df = rawData_to_df(self.event_obj['RawData'])
        rawAcc = self.rawData_df.iloc[:, 4:].copy(deep=True)
        offset = sp.bit_to_offset(self.offset)
        rawAcc = sp.shift(rawAcc, -np.array(offset), rawAcc.columns)
        rawAcc = sp.insert_time_column(rawAcc, sigFs=200)
        gyroSignal = self.rawData_df.iloc[:, 1:4].copy(deep=True).to_numpy()
        gyroSignal = (self.calibrationInfo['OperationalMat'] @ gyroSignal.T).T
        gyroSignal = pd.DataFrame(gyroSignal, columns=self.rawData_df.iloc[:, 1:4].columns)
        gyroSignal = sp.insert_time_column(gyroSignal, sigFs=200)
        ClearmlUtility.report_plotly(title="Raw Signal", plotly_object=Visualisation.df_to_plot_plotly(rawAcc))
        plt.close()
        ClearmlUtility.report_plotly(title="Gyro Signal", plotly_object=Visualisation.df_to_plot_plotly(gyroSignal))
        plt.close()

    def getCalibObj(self):
        self.calibrationInfo = self.event_obj["CalibrationData"]
        self.calibrationInfo["Offset"] = self.offset
        self.calibrationInfo["DeviceID"] = self.DeviceID
        self.calibrationInfo["SerialNumber"] = self.SerialNumber
        if "calibration" not in self.task.artifacts:
            ClearmlUtility.upload_artifact(task=self.task, artifact_name="calibration", artifact_object=self.calibrationInfo)
        if ("Calculations" in self.calibrationInfo and "Ax" in self.calibrationInfo["Calculations"] and
            self.calibrationInfo["Calculations"]["Ax"] is not None):
                self.task.add_tags(["Braking", ])

    def reportRotatedSignal(self):
        self.rotated_sig = sp.rotate_signal(self.rawData_df, self.calibrationInfo["OperationalMat"], "FRD",
                                       self.calibrationInfo["AxesOrientation"], offset=self.offset)
        rotated_sig = sp.insert_time_column(self.rotated_sig.copy(deep=True), self.sigFs)
        ClearmlUtility.report_plotly(title="Rotated Signal",
                                     plotly_object=Visualisation.df_to_plot_plotly(rotated_sig))
        plt.close()

    def reportDamageInsight(self):
        self.logger.PrintLog(LogLevel.Info, f"DamageInsight: {self.event_obj['Insight'].keys()}, Task: {str(self.task.status)}")
        crashDict = {k: v for k, v in self.event_obj["Insight"].items() if k in ["IsCrash", "Confidence", "Mechanism",
                                                                                 "Theta", "Dv"]}
        ClearmlUtility.upload_artifact(task=self.task, artifact_name="crash", artifact_object=crashDict)
        self.task.mark_started(force=True)
        self.task.add_tags(["Crash", ]) if crashDict["IsCrash"] else self.task.add_tags(["NoCrash", ])
        self.isCrash = True if crashDict["IsCrash"] else False
        if self.isCrash:
            mechanism = crashDict["Mechanism"]
            if mechanism != "Rollover":
                airbag_obj = self.event_obj['InsightsData'][0]['AirBagDeploy']
                ClearmlUtility.upload_artifact(task=self.task, artifact_name="AirBadDeploy", artifact_object=airbag_obj)
                if any([v['Deployed'] for k, v in airbag_obj.items()]):
                    self.task.add_tags(["AirBagDeploy", ])
                damagesResult = {k: v for k, v in self.event_obj['InsightsData'][0].items() if k in ["Final", "Added",
                                                                                                  "Removed"]}
                ClearmlUtility.upload_artifact(task=self.task, artifact_name="Damages", artifact_object=damagesResult)
                fig = Visualisation.plot_damage_cells(damagesResult["Final"])
                ClearmlUtility.report_matplotlib_figure(task=self.task, title=f"Final Damage cells in {mechanism} mechanism",
                                                        figure=fig, report_image=True)
                if len(damagesResult["Added"]) > 0 or len(damagesResult["Removed"]) > 0:
                    plt.close()
                    final = list((set(damagesResult["Final"]) -
                                  set(damagesResult["Added"])).union(set(damagesResult["Removed"])))
                    fig = Visualisation.plot_damage_cells(final)
                    plt.suptitle(f"Damage cells in {mechanism} mechanism before post-process", fontsize=20)
                    ClearmlUtility.report_matplotlib_figure(task=self.task,
                                                            title=f"Damage cells in {mechanism} mechanism before post-process",
                                                            figure=fig, report_image=True)
                    time.sleep(1)
                    plt.close()
                else:
                    plt.suptitle(f"Damage cells in {mechanism} mechanism before post-process", fontsize=20)
                    ClearmlUtility.report_matplotlib_figure(task=self.task,
                                                            title=f"Damage cells in {mechanism} mechanism before post-process",
                                                            figure=fig, report_image=True)
                    plt.close()
            else:
                self.task.add_tags(["Rollover", ])


    def reportMedicalInsight(self):
        # self.logger.PrintLog(LogLevel.Info, f"MedicalInsight: {self.event_obj['Insight']}, Task: {str(self.task.status)}")
        mechanism = self.event_obj["Insight"]["Mechanism"]
        if mechanism != "Rollover":
            MedicalCriteria = self.event_obj["Insight"]["MedicalCriteria"]
            for key1, val1 in MedicalCriteria.items():
                ClearmlUtility.upload_artifact(task=self.task,
                                               artifact_name=f"Medical criteria {mechanism} mechanism occ_{key1}",
                                               artifact_object=val1)


            occupants = self.event_obj["InsightsData"][0]["Occupants"]
            for occ, val in occupants.items():
                if 'VirtualSensors' in val:
                    ClearmlUtility.report_plotly(task=self.task,
                                                 title=f"Virtual Sensors for occ_{occ} in {mechanism} mechanism",
                                                 plotly_object=Visualisation.df_to_plot_plotly(
                                                     pd.DataFrame.from_dict(val['VirtualSensors']), time_axis=False))

    def addTagsBasedOnAllocation(self):
        rot_sig = self.rotated_sig[self.clearml_config["acc_columns"]]
        maxG = np.max(np.abs(rot_sig.to_numpy()))
        if self.AllocatedTo in self.clearml_config["HighImpactAllocation"] and self.isCrash:
            if maxG > self.clearml_config["HighImpactMaxG"]:
                self.task.add_tags(["forManualIntervention", ])
        elif self.AllocatedTo in self.clearml_config["LowImpactAllocation"]:
            if self.isCrash:
                self.task.add_tags(["forManualIntervention", ])
            else:
                delta_v = np.cumsum(((rot_sig.to_numpy() * 9.8) / self.sigFs) * 3.6, axis=0)
                XY_max = []
                i = 0
                delta = self.clearml_config["dv_duration"]
                for i in range(1, delta_v.shape[0] - delta):
                    temp = delta_v[i: i + delta, :] - delta_v[i - 1]
                    XY_max.append(np.max(np.abs(temp), axis=0))
                maxXY = np.max(np.array(XY_max))
                if maxXY > self.clearml_config["LowImpactDv"]:
                    self.task.add_tags(["forManualIntervention", ])
        else:
            pass

    def reportPreviosEvents(self):
        veh_type = self.event_obj["CarIdentification"]
        self.logger.PrintLog(LogLevel.Info, f"CarIdentification: {self.event_obj['CarIdentification']}, Task: {str(self.task.status)}")
        device_events = self.event_obj["DeviceEvents"]
        if veh_type is None:
            veh_type = ""
        elif "VehicleType" not in veh_type:
            veh_type = veh_type["Model"]
        else:
            veh_type = veh_type["VehicleType"]
            if not isinstance(veh_type, str):
                veh_type = ""
        if not isinstance(device_events, list):
            raise TypeError("DeviceEvents should be list")
        if len(device_events) > 0:
            events_table = pd.DataFrame(columns=["EventID", "ReceivingTime", "EventLocation", "IsCrash",  "VehicleType"])
            for i, event in enumerate(device_events):
                events_table.at[i, "EventID"] = event["EventID"]
                events_table.at[i, "ReceivingTime"] = str(event["ReceivingTime"])
                coordinates = event["EventLocation"]['coordinates'][::-1]
                events_table.at[i, "EventLocation"] = f"{coordinates[0]}, {coordinates[1]}"
                events_table.at[i, "IsCrash"] = event["IsCrash"]
                events_table.at[i, "VehicleType"] = veh_type
            events_table["TimeFromLastEvent_Hours"] = round((pd.to_datetime(self.receivingTime)
                                                 - pd.to_datetime(events_table["ReceivingTime"])) / pd.Timedelta(hours=1))
            events_table.sort_values(by="ReceivingTime", ascending=False, inplace=True , ignore_index=True)
            events_table = events_table[["EventID", "TimeFromLastEvent_Hours", "ReceivingTime", "EventLocation", "IsCrash",  "VehicleType"]]

            self.clLogger.report_table("z. Device History", "Events for last 72 hours ", iteration=0, table_plot=events_table)
            ClearmlUtility.upload_artifact(task=self.task, artifact_name=f"Device history",
                                           artifact_object=pd.DataFrame.to_dict(events_table, orient='index'))

    def run(self):
        try:
            self.getMetaData()
            self.connect_to_task()
            self.reportLocation()
            self.getCalibObj()
            self.getRawData()
            self.reportRotatedSignal()
            if not self.event_obj["Insight"]["IsSignalValid"]:
                ClearmlUtility.upload_artifact(task=self.task, artifact_name=f"UnvaldityReason",
                                           artifact_object=self.event_obj["Insight"]["SignalInvalidityReason"])
                self.task.add_tags(["SignalNotValid"])
            else:
                if "IsAmbulanceDispatched" in self.event_obj['Insight'] and self.event_obj['Insight']["IsAmbulanceDispatched"]:
                    self.task.add_tags(["AmbulanceDispatched"])
                self.reportDamageInsight()
                if self.event_obj["Insight"]['IsCrash']:
                    self.reportMedicalInsight()
                self.addTagsBasedOnAllocation()
                if "CarIdentification" in self.event_obj and "DeviceEvents" in self.event_obj:
                    self.reportPreviosEvents()
            self.task.flush(wait_for_uploads=True)
            self.task.completed(self.task)
            self.logger.PrintLog(LogLevel.Info, "ClearML: Successfully finished process")
            return True
        except Exception as ex:
            self.task.flush(wait_for_uploads=True)
            self.task.completed(self.task)
            self.logger.PrintLog(LogLevel.Warning, f"ClearML: finished with warning : {ex}")
            self.logger.PrintLog(LogLevel.Warning, f"ClearML: full traceback : {traceback.format_exc()}")
            self.task.flush(wait_for_uploads=True)
            self.task.completed(self.task)
            return False







