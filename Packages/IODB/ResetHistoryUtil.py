from IODB.CommonConstants import *


class ResetHistoryUtil:
    @staticmethod
    # returns <bool, bool> - <is reset needed, should ignore current>
    def IsResetNeeded(reset_flag_obj):
        if reset_flag_obj is None:
            return False, None

        if (type(reset_flag_obj) is not dict or \
                "Behavior" not in reset_flag_obj):
            return False, None

        __flagBehavior = reset_flag_obj["Behavior"]

        if (type(__flagBehavior) is not str or \
                (__flagBehavior != Reset_Behavior_Ignore_History and \
                 __flagBehavior != Reset_Behavior_Ignore_Current)):
            return False, None

        return True, __flagBehavior == Reset_Behavior_Ignore_Current
