##ALARMS
##ALARM_MAP
##check_alarms()
##process_alarm_changes()

# Список словарей аварий
# или реестр аварий

ALARMS = [
    {
        "id": "T1_HIGH",
        "name": "Перегрев T1",
        "check": lambda d: d.get("T1", 0) > 30,
        "level": "HIGH"
    },
    {
        "id": "T1_LOW",
        "name": "Переохлаждение T1",
        "check": lambda d: d.get("T1", 0) < 5,
        "level": "LOW"
    },
    {
        "id": "FAN_FAIL",
        "name": "Вентилятор не работает",
        "check": lambda d: d.get("n1", 0) < 95,
        "level": "CRITICAL"
    },
    {
        "id": "ALARM",
        "name": "Общая авария",
        "check": lambda d: d.get("Alarms", 0) != 0,
        "level": "CRITICAL"
    }
]

########################################
# @brief возвращает список list активных аварий
# 
#
########################################
def check_alarms(data):
    active = []

    for alarm in ALARMS:
        try:
            if alarm["check"](data):
                active.append(alarm)
        except:
            pass

    return active


###################################################
# Критичность аварий
###################################################
def level_icon(level):
    if level == "CRITICAL":
        return "🔴 CRITICAL"
    elif level == "HIGH":
        return "🟠 HIGH"
    else:
        return "🟡 LOW"

###################################################
# Активность аварий
###################################################
def format_state(state):
    if state == "ON":
        return "🔴 АКТИВНА"
    else:
        return "🟢 СНЯТА"

