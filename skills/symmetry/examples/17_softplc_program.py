"""Программа «ПЛК» для примера 17 (сепаратор): LIC-100, PIC-100, блокировки и диагностика клапана.
Запуск: python scripts/softplc.py --ua opc.tcp://localhost:4841/symmetry/ --tags examples/17_plc_tags.csv
        --program examples/17_softplc_program.py --log plc.csv
Логика переносится в ST один к одному (PID → блок ПИД ПЛК, TON → TON, SR → SR).
Ключи ALM.* — внутренние переменные программы (в модель не уходят, пишутся в журнал).
"""
from softplc import PID, TON, SR

SHOW = ["LT100.PV", "PT100.PV", "LV100.CMD", "LV100.POS", "ALM.LV_FAULT", "XV100.OPEN"]

# уставки (в реальном ПЛК — переменные HMI)
SP_LEVEL = 50.0        # %
SP_PRESS = 4000.0      # кПа
LSHH = 60.0            # % — закрыть входной клапан (низко, чтобы сработало в демо)
LSHH_RESET = 55.0      # % — разрешить открытие (после квитирования в реальной системе)
DEV_LIM = 10.0         # % — рассогласование команда/положение клапана
DEV_TIME = 15.0        # с

# уровень: PV растёт → открывать клапан воды (direct); давление: PV растёт → открывать клапан газа (direct)
lic = PID(kp=2.0, ti=300.0, pv_lo=0, pv_hi=100, direct=True)
pic = PID(kp=1.0, ti=60.0, pv_lo=3000, pv_hi=5000, direct=True)
t_hh = TON(3.0)          # подтверждение LSHH 3 с (защита от шума)
t_dev = TON(DEV_TIME)    # рассогласование LV-100
trip = SR()
lv_fault = SR()


def init(io):
    lic.bumpless(io["LV100.CMD"])          # безударный старт от текущего положения
    pic.bumpless(io["PV100.CMD"])
    io["ALM.LSHH"] = False
    io["ALM.LV_FAULT"] = False


def scan(io, dt):
    # диагностика исполнительного механизма: команда ≠ положение дольше DEV_TIME
    dev = abs(io["LV100.CMD"] - io["LV100.POS"]) > DEV_LIM
    io["ALM.LV_FAULT"] = lv_fault(t_dev(dev, dt), False)          # с фиксацией (сброс — квитирование)
    # блокировка по уровню
    io["ALM.LSHH"] = t_hh(io["LT100.PV"] > LSHH, dt)
    tripped = trip(io["ALM.LSHH"] or io["ALM.LV_FAULT"], io["LT100.PV"] < LSHH_RESET and not io["ALM.LV_FAULT"])
    io["XV100.OPEN"] = not tripped
    io["LV100.CMD"] = round(lic(SP_LEVEL, io["LT100.PV"], dt), 3)
    io["PV100.CMD"] = round(pic(SP_PRESS, io["PT100.PV"], dt), 3)
