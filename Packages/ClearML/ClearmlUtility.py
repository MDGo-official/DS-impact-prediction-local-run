import plotly
import matplotlib.figure
import matplotlib.pyplot as plt
from clearml import Task
from Utils import DSLogger, LogLevel


class ClearmlUtility:

    @classmethod
    def get_task(cls, project_name, task_name, reset=False):
        cls.logger = DSLogger("ClearmlUtility")
        if type(project_name) is not str:
            raise ValueError("project_name is not a valid str")
        if type(task_name) is not str:
            raise ValueError("task_name is not a valid str")
        try:
            cls.task = Task.get_task(project_name=project_name, task_name=task_name)
            if cls.task is None:
                cls.logger.PrintLog(LogLevel.Info, f"There is no such task {task_name}")
            else:
                # cls.logger.PrintLog(LogLevel.Info, "Successfully get the task")
                cls.task.started()
                cls.clearml_logs = cls.task.get_logger()
                if reset:
                    cls.task.reset(set_started_on_success=True, force=True)
                    cls.task.reload()
            return cls.task
        except Exception as e:
            msg = f"Cannot connect to clearml server, cause of: {e}"
            cls.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    @classmethod
    def task_init(cls, project_name, task_name, task_type=Task.TaskTypes.inference, reuse_last_task_id=True,
                  auto_connect_arg_parser=True, auto_connect_frameworks=True, auto_resource_monitoring=True,
                  auto_connect_streams=True):
        cls.logger = DSLogger("ClearmlUtility")
        if type(project_name) is not str:
            raise ValueError("project_name is not a valid str")
        if type(task_name) is not str:
            raise ValueError("task_name is not a valid str")
        try:
            cls.task = Task.init(project_name=project_name, task_name=task_name, reuse_last_task_id=reuse_last_task_id,
                                 task_type=task_type, auto_connect_arg_parser=auto_connect_arg_parser,
                                 auto_connect_frameworks=auto_connect_frameworks,
                                 auto_resource_monitoring=auto_resource_monitoring,
                                 auto_connect_streams=auto_connect_streams)
            cls.clearml_logs = cls.task.get_logger()
            cls.logger.PrintLog(LogLevel.Info, "Successfully initialize new task")
            return cls.task
        except Exception as e:
            msg = f"Cannot connect to clearml server, cause of {e}"
            # cls.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    @classmethod
    def _check_task(cls, task):
        if not hasattr(ClearmlUtility, "logger"):
            cls.logger = DSLogger("ClearmlUtility")
        if task is not None:
            if type(task) is not Task:
                raise ValueError("task is not a valid clearml task")
            cls.task = task
            cls.task.started()
            cls.clearml_logs = cls.task.get_logger()

    @classmethod
    def add_object_task(cls, object, name=None, task=None):
        cls._check_task(task)
        if type(object) is not dict:
            raise ValueError("object is not valid dict")
        if type(name) is not str and name is not None:
            raise ValueError("name is not valid str")
        try:
            cls.task.mark_started(force=True)
            cls.task.connect(object, name=name)
            cls.task.flush(wait_for_uploads=True)
            # cls.logger.PrintLog(LogLevel.Info, f"Object {name} was upload successfully")
        except Exception as e:
            msg = f"Cannot connect to clearml server, cause of {e}"
            # cls.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    @classmethod
    def upload_artifact(cls, artifact_name, artifact_object, task=None):
        cls._check_task(task)
        if artifact_name is None or type(artifact_name) is not str:
            raise ValueError("artifact_name is not a valid str")
        if artifact_object is None:
            raise ValueError("artifact_object is not defined")
        try:
            cls.task.mark_started(force=True)
            res = cls.task.upload_artifact(artifact_name, artifact_object)
            cls.task.flush(wait_for_uploads=True)
            if res:
                cls.logger.PrintLog(LogLevel.Info, f"Artifact {artifact_name} was upload successfully")
            else:
                cls.logger.PrintLog(LogLevel.Info, f"Artifact {artifact_name} failed to upload")
        except Exception as e:
            msg = f"Cannot connect to clearml server, cause of {e}"
            cls.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    @classmethod
    def report_plotly(cls, title, plotly_object, series="", iteration=0, task=None):
        cls._check_task(task)
        if title is None or type(title) is not str:
            raise ValueError("title is not defined or not a valid str")
        if type(plotly_object) is not plotly.graph_objects.Figure:
            raise ValueError("plotly_object is not valid plotly figure")
        try:
            cls.task.mark_started(force=True)
            cls.clearml_logs.report_plotly(title=title, series=series, iteration=iteration, figure=plotly_object)
            cls.task.flush(wait_for_uploads=True)
            cls.logger.PrintLog(LogLevel.Info, f"Successfully report plotly object for {title}, task.status: {cls.task.get_status()}")
        except Exception as e:
            msg = f"Cannot connect to clearml server, cause of {e}"
            cls.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    @classmethod
    def report_matplotlib_figure(cls, title, figure, report_image=True, series="", iteration=0, task=None):
        cls._check_task(task)
        if title is None or type(title) is not str:
            raise ValueError("title is not defined or not a valid str")
        if type(figure) is not matplotlib.figure.Figure:
            raise ValueError("figure is not valid matplotlib figure")
        try:
            cls.task.mark_started(force=True)
            cls.clearml_logs.report_matplotlib_figure(title=title, series=series, iteration=iteration, figure=figure,
                                                  report_image=report_image)
            cls.task.flush(wait_for_uploads=True)
            cls.logger.PrintLog(LogLevel.Info, f"Successfully report matplotlib object for {title}")
        except Exception as e:
            msg = f"Cannot connect to clearml server, cause of {e}"
            cls.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    @classmethod
    def report_html_url(cls, title, url, series="", iteration=0, task=None):
        cls._check_task(task)
        if type(title) is not str:
            raise ValueError("title is not a valid str")
        if type(url) is not str:
            raise ValueError("url is not valid str")
        try:
            cls.task.mark_started(force=True)
            cls.clearml_logs.report_media(title=title, series=series, iteration=iteration, url=url)
            cls.task.flush(wait_for_uploads=True)
            # cls.logger.PrintLog(LogLevel.Info, f"Successfully report {title}")
            return cls.clearml_logs
        except Exception as e:
            msg = f"Cannot connect to clearml server, cause of {e}"
            cls.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    @classmethod
    def complete_task(cls, task=None):
        cls._check_task(task)
        try:
            cls.task.completed()
            cls.logger.PrintLog(LogLevel.Info, "Successfully completed clearml task")
        except Exception as e:
            msg = f"Cannot connect to clearml server, cause of {e}"
            cls.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    @classmethod
    def close_task(cls, task=None):
        cls._check_task(task)
        try:
            cls.task.close()
            cls.logger.PrintLog(LogLevel.Info, "Successfully close clearml task")
        except Exception as e:
            msg = f"Cannot connect to clearml server, cause of {e}"
            cls.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)



