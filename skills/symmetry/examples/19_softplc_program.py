"""ПЛК насосной (пример 19): двухпозиционное управление насосом по уровню + LAHH + «нет расхода при работе».
python scripts/softplc.py --ua opc.tcp://localhost:4841/symmetry/ --tags examples/19_plc_tags.csv
       --program examples/19_softplc_program.py --sim-time --log plc19.csv
"""
from softplc import TON, SR

SHOW = ["LT200.PV", "FT201.PV", "P1.RUN", "P1.RUNFB", "ALM.LAHH", "ALM.P1_NOFLOW"]
L_START, L_STOP, LAHH = 60.0, 40.0, 75.0
run = SR()                 # пуск по верхнему уровню, стоп по нижнему (гистерезис)
t_noflow = TON(10.0)       # насос включён, а расхода нет 10 с → неисправность
t_lahh = TON(2.0)
fault = SR()


def init(io):
    run.q = bool(io["P1.RUNFB"])
    io["ALM.LAHH"] = False
    io["ALM.P1_NOFLOW"] = False


def scan(io, dt):
    io["ALM.LAHH"] = t_lahh(io["LT200.PV"] > LAHH, dt)
    io["ALM.P1_NOFLOW"] = fault(t_noflow(io["P1.RUNFB"] and io["FT201.PV"] < 3.0, dt), False)
    cmd = run(io["LT200.PV"] > L_START, io["LT200.PV"] < L_STOP)
    io["P1.RUN"] = cmd and not io["ALM.P1_NOFLOW"]
