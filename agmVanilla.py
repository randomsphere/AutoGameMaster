# -*- coding: utf-8 -*-
from AutoGameMaster.agmBase import *

import enum

# =============================================================================
# Enums + Auxiliar Functions
# =============================================================================

class Tags(enum.Enum):
    DMG  = 0x00
    ATK  = 0x01
    AOE  = 0x02
    DOT  = 0x03

def repTurnUses(turns, uses):
    res = []

    if turns != None and turns > 0: res.append(str(turns) + "T")
    if uses != None and uses > 0:  res.append(str(uses) + "X")

    return "("+"/".join(res)+")"

# =============================================================================
# Gauge Stuff
# =============================================================================

class GaugeDef(EventHolder):

    def __init__(self, name):
        super().__init__()
        self.name = name
        self.val  = 0

    def inc(self, inc):
        self.val = self.val + inc

    def getValue(self):
        return self.val

    def __str__(self, name):
        return self.name + " " + ("+" if self.val >= 0 else "") + str(self.val)


class GaugeIntCounter(GaugeDef):

    def __init__(self, name, val = 0, minval=0, maxval=None):
        super().__init__(name)

        self.min = minval
        self.max = maxval

    def inc(self, inc, isBounded = True):
        self.var += inc

        if isBounded:
            if self.minval != None: max(self.minval, self.var)
            if self.maxval != None: min(self.maxval, self.var)

    def __str__(self):
        return self.name + " [ " + str(self.val) + (" / " + str(self.max)) if self.max != None else "" + " ]"


class GaugeHP(GaugeIntCount):

    def __init__(self, lifebars=None):
        super().__init__("HP")

        if type(lifebars) == int:
            self.val    = lifebars
            self.maxval = lifebars
            self.lifebars == None

        elif type(lifebars) == list:
            self.lifebars = lifebars
            self.lbMax    = len(lifebars)-1
            self.val      = self.lifebars[0]
            self.maxval   = self.val


    def popLifebar(self):
        if self.lifebars == None: return None
        res = self.lifebars.pop()

        self.maxval = res
        self.val    = self.maxval

        if self.lifebars == []: self.lifebars = None

        return res


    def __str__(self):
        return "HP" + (f' [ {1} / {2} ]' if len(self.lbs) > 0 else '')
                            + f' [ {self.val} / {self.maxval} ]'


class GaugeGuard(GaugeDef):

    def __init__(self):
        super().__init__("grd")

    @agmDecor.EvMethod('action'):
    def onAttack(self):
        ...


class GaugeCharge(GaugeDef):

    def __init__(self):
        super().__init__("chg")

    @agmDecor.EvMethod('action')
    def onChargeStuff(self):
        ...



# =============================================================================
# Useful Functions
# =============================================================================

def apply_damage_modifier(dicc, inc, p):
    values = dicc.get(p, [0, 1., 1.])
    if type(inc) == int:
        dicc[0] += inc
    else:
        if inc > 1.: values[1] += inc - 1.
        elif inc >= 0.: values[2]*= 1. - inc

    dicc[p] = values
    return dicc

def deal_damage(attackers, targets, dmg, mod, tags={}):
    pass

# =============================================================================
# Default Nonspells
# =============================================================================

@agmDecor.ActionCreator("Attack", 'Deal [AP] damage to a single target.')
def attackCommand():

    def define():
        pass

    def execute():
        pass

    return define, execute


@agmDecor.ActionCreator("Guard", 'Reduce damage taken this turn by [GP].')
def guardCommand():

    def define():
        pass

    def execute():
        pass

    return define, execute


@agmDecor.ActionCreator("Charge", 'Gain [CP] charge.')
def chargeCommand():

    def define():
        pass

    def execute():
        pass

    return define, execute


@agmDecor.ActionCreator("Extend", 'Select an ally and await a turn. Next turn, such ally is revived for as much HP as 20% of their MAX HP (twice if the user is a [HEAL]).')
def extendCommand():

    def define():
        pass

    def execute():
        pass

    return define, execute


# =============================================================================
# Vanilla Statuses
# =============================================================================

class AttackUp(Status):

    def __init__(self, isPerm = False, isVisible = True, conditions=[]):
        super().__init__("Increases damage dealt by its potency.", isPerm, isVisible, conditions)

        self.potency = 0


    def setPotency(self, potency):
        if type(self.potency) == int and self.potency <= 0: return
        if type(self.potency) == float and self.potency < 1.: return
        self.potency = potency


    def getTitle(self):
        pot = str(self.potency) if type(self.potency) == int else ""
        return "ATKUP [" + pot + "] " + repTurnUses(self.turns, self.count)


    @agmDecor.EvMethod('action')
    async def buffStuff(self, action):
        apply_damage_modifier(action.vars, potency, 0)
