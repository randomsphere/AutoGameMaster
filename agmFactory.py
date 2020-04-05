from AutoGameMaster.agmBase import *
from importlib import import_module
import copy

def addUnitLib(moduleName):
    globals()['unitLib' + moduleName] = import_module('AutoGameMaster.units.' + moduleName)

def removeUnitLib(moduleName):
    del globals()[moduleName]

def createGenericUnit(moduleName):
    unitLib = globals()['unitLib' + moduleName]

    res = Unit()

    res.ROLE = unitLib.ROLES
    res.NAME = unitLib.NAME

    res.AP   = unitLib.AP
    res.GP   = unitLib.GP
    res.CP   = unitLib.CP

    res.actions = [NonspellType(), SpellType()]
    res.actions[0].unit = res
    res.actions[1].unit = res

    for GAUGE in unitLib.GAUGES:
        res.gauges[GAUGE.name] = GAUGE

    nonspells = res.actions[0]
    for NONSPELL in (attackCommand, guardCommand, chargeCommand, extendCommand):
        res.actions[0].commands.append(NONSPELL().setUnit(res).setComType(nonspells))

    for PASSIVE in unitLib.PASSIVES:
        res.passives.append(PASSIVE().setUnit(res))
        newPassive.unit = res

    spells = res.actions[1]
    for SPELL in unitLib.SPELLS:
        res.actions[1].commands.append(SPELL().setUnit(res).setComType(spells))

    unitLib.special_conditions(res)

    return res
