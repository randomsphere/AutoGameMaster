# -*- coding: utf-8 -*-
from AutoGameMaster.agmVanilla import *
import asyncio

'''
@agmDecor.ActionCreator('name', 'desc')
def testAction():
    async def define(self, a,b):
        ...

    async def execute(self, a):
        ...

    async def exampleMethod(self, *args):
        ...

    return define, execute, exampleMethod
'''

ROLES = []
NAME  = "Placeholder"

AP = "d20"
GP = "d20"
CP = "5"

GAUGES    = [GaugeHP(90), GaugeGuard(), GaugeCharge()]
PASSIVES  = []
NONSPELLS = []
SPELLS    = []


def special_conditions(unit):
    pass
