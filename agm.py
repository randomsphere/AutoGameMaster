# -*- coding: utf-8 -*-
from Collections import defaultdict
from react_msg import ReactMsg

import asyncio
import nest_asyncio
nest_asyncio.apply()

# =============================================================================
# Event Object + Deletable Object
# =============================================================================


class Event(object): 
  
    def __init__(self): 
        self.__eventhandlers = [] 
      
    def add_event(self, handler): 
        self.__eventhandlers.append(handler)
        self.__eventhandlers.sort(key = lambda x : x.preference)
        return self
      
    def rev_event(self, handler): 
        self.__eventhandlers.remove(handler) 
        return self
      
    async def __call__(self, *args, **keywargs): 
        for eventhandler in self.__eventhandlers: 
            await eventhandler(*args, **keywargs)

class DelObj:
    
    def __init__(self):
        self.__isdel = False
    
    def isDeleted(self):
        return self.__isdel
    
    def delete(self):
        self.__isdel = True


# =============================================================================
# Basic components 
# =============================================================================


class Action(DelObj):
    
    def __init__(self, code_def, code_exc):
        super().__init__(self)
        self.code_def = code_def
        self.code_exc = code_exc
        self.vars     = defaultdict(None)

    def define(self, unit):
        self.vars = self.code_def(unit)
        return self.vars
    
    def execute(self, unit):
        if self.vars["is_usable"] == True:
            self.code_exc(unit, self.vars)


class EventHolder(DelObj):
    
    def __init__(self, unit, name):
        super().__init__(self)
        self.unit = unit
        self.name = name
        self.start()
    
    def __bfEvs(self, isStart):
        for ev in dir(self):
            event = getattr(self, ev)
            if getattr(event, "evType", None) in {None, "on_instance", "on_deletion"}:continue
            
            target = None
            if ev.isOnUnit:  target = self.unit
            else:            target = self.unit.team.bf
            
            if isStart: target.addEvent(event)
            else:       target.revEvent(event)
    
    def start(self):
        self.__bfEvs(True)
        if getattr(self, "on_instance", None) != None: getattr(self, "on_instance")()
    
    def remove(self):
        self.__op(False)
        if getattr(self, "on_deletion", None) != None: getattr(self, "on_deletion")()


class Status(EventHolder):
    
    def __init__(self, unit, name, desc, isPerm = False, isVisible = True):
        self.desc = desc
        self.vars = dict()
        
        self.isVisible = isVisible
        self.isPerm    = isPerm
        
        self.turns     = None
        self.count     = None
        
        super().__init__(self, unit, name)
    
    def tick(self):
        
        if self.turns != None:
            self.turns-=1            
            if self.turns > 0:
                return self.turns
            elif self.turns == 0:
                self.remove()
                self.delete()
                return 0
        
        return -1
    
    def consume(self):
        
        if self.count != None:
            self.count-=1            
            if self.count > 0:
                return self.count
            elif self.count == 0:
                self.remove()
                self.delete()
                return 0
        
        return -1
    
    def show(self):
        return ""


class Command(EventHolder):
    
    def __init__(self, unit, name, desc, action, cd = None):
        self.action   = action
        self.isUsable = 0
        
        super().__init__(self, unit, name, desc)
        
    async def use(self):
        if self.isUsable > 0: return -1
        


class CommandType(EventHolder):
    
    def __init__(self, unit, name, commands):
        self.commands = commands
        self.isUsable = 0
        super().__init__(self, unit, name, "", None, cd=0)


# =============================================================================
# Gauge Stuff
# =============================================================================

class GaugeDef(DelObj):
    
    def __init__(self, unit, name, val = 0, code = defaultdict(None)):
        self.unit = unit
        self.name = name
        self.val  = val
        
        super().__init__(self)
        
    def inc(self, inc):
        self.val = self.val + inc
    
    def getValue(self):
        return self.val
    
    def show(self):
        return self.name + " " + ("+" if self.val >= 0 else "") + str(self.val)

class GaugeTurn(GaugeDef):
    
    def __init__(self, unit, name, val = 0):
        super().__init__(self, unit, name, val = val, code = None)
    
    def show(self):
        return self.name + " [" + str(self.val) + " ]" 

class GaugeHP(GaugeDef):
    
    def __init__(self, unit, name, val = 0, minval = None, maxval = None, lb = 0, maxlb = 0):
        super().__init__(self, unit, name, val = val, code = None)
        self.minval = minval
        self.maxval = maxval
        self.lb = lb
        self.maxlb = maxlb

    def inc(self, inc, isBounded = True):
        self.val += inc
        
        if isBounded:
            if self.minval != None:
                self.val = max(self.val, self.minval)
            if self.maxval != None:
                self.val = min(self.maxval, self.val)
        
        return self.val
    
    def getLifebars(self):
        return self.lb
    
    def show(self):
        return self.name + (" [ " + "O"*self.lb + "-"*(self.maxlb-self.lb) + " ]" if self.maxlb > 0 else "") + " [ " + str(self.val) + " / " + str(self.maxval) + " ]"
            

# =============================================================================
# Unit Stuff
# =============================================================================

class Unit(DelObj):
    
    def __init__(self, team):
        self.ROLE     = []
        self.AP       = "1d20"
        self.GP       = "1d20"
        self.CP       = "5"
        
        self.hp       = GaugeHP(self, "HP", val = 90, minval = 0, maxval = 90)
        self.guard    = GaugeDef(self, "Guard", val = 0)
        self.charge   = GaugeDef(self, "Charge", val = 0)
        
        self.turnPriority   = 0
        self.targetPriority = 0
        self.acts           = 0
        
        self.owner    = None
        self.team     = team
        
        self.gauges    = []
        self.statuses  = []
        self.passives  = []
        self.actions   = []
        
        self.events    = dict()
        
    
    # Event & Phase methods        
    async def turnCycle(self):
        await self.team.bf.callEvent("on_unit_turn")
        
        while self.acts > 0:
            await self.owner.turnCycle(self)
            self.acts -= 1

    async def callEvent(self, event, *args):
        ev = self.events.get(event, None)
        if ev is not None: await ev(*args)
    
    def addEvent(self, event):
        if self.events.get(event.evType, None) != None: self.events[event.evType].add_event(event)
        else:                                           self.events[event.evType] = Event().add_event(event)
    
    def revEvent(self, event):
        if self.events.get(event.evType, None) != None: self.events[event.evType].rev_event(event)
    
    
    # Prints
    def showBase(self):
        res = ""
        if len(self.ROLE) > 0 : res +=  "[" + "/".join(self.ROLE) + "] "
        res += self.name + " - "
        
        if self.hp != None :     res += self.hp.show() + " / "
        if self.guard != None :  res += self.guard.show() + " / "
        if self.charge != None : res += self.charge.show() + " / "
        
        if len(self.gauges) > 0 : res += " / ".join(g.show() for g in self.gauges)
        
        return res
    
    
    def showStatuses(self):
        res = "STATUSES: "
        per_stats = []
        nor_stats = []
        
        for status in self.statuses:
            
            if status.is_visible: continue
            
            if status.is_perm: per_stats.append(status)
            else:              nor_stats.append(status)
                
        if len(per_stats) > 0: res += "{ " + ", ".join(x.show() for x in per_stats) + " } "
        if len(nor_stats) > 0: res += ", ".join(x.show() for x in nor_stats)
        return res



# =============================================================================
# Team & Battlefields
# =============================================================================

class Team(DelObj):
    
    def __init__(self, name, battlefield):
        self.name        = name
        self.bf          = battlefield

        self.units       = []
        self.patterns    = []
        self.gauges      = []
        
        super().__init__(self)
        
    def showUnits(self, showStatuses = False):
        res = [unit.showBase() + ("\n" + unit.showStatuses() if showStatuses else "") for unit in self.units]
        return res
    
    def showPatterns(self):
        return "\n".join(p.show() for p in self.patterns)
    

class Battlefield(DelObj):
    
    def __init__(self, session):
        self.turn     = GaugeTurn(self, "Turn", val=0, code=None)
        self.name     = "Battlefield"
        self.teams    = [Team("<{ Players' Side }>", self), Team("<{ Enemies' Side }>", self)]
        self.session  = session
        
        self.events   = dict()
        
        super().__init__(self)
    
    
    # Event & Phase methods
    async def callEvent(self, event, *args):
        ev = self.events.get(event, None)
        if ev is not None: await ev(*args)
    
    def addEvent(self, event):
        if self.events.get(event.evType, None) != None: self.events[event.evType].add_event(event)
        else:                                           self.events[event.evType] = Event().add_event(event)
    
    def revEvent(self, event):
        if self.events.get(event.evType, None) != None: self.events[event.evType].rev_event(event)
    
    async def turnPhaseCycle(self):
        for team in self.teams:
            for unit in team.units:
                unit.acts += 1
        self.turn.inc(1)
        
        while True:
            unit = self.__calculateTurnOrder()
            if unit == None: break
            await unit.turnCycle()
            
    
    # System functions
    def searchPossibleTargets(teams=[], targetPriority=True):
        res = []
        for team in teams:
            
            if not targetPriority:
                res += [team.units]
            
            else:
                units = defaultdict(list)
                for unit in team.units: units[unit.targetPriority].append(unit)
                res += [max(units.items())[1]] 
        
        return res
    
    async def damageTarget(damage, targets):
        
        for t in targets:
            if t.isDeleted():continue
            pass
    
    
    #Printing Functions
    def showHeader(self):
        res = self.name
        for gauge in self.gauges:
            res += gauge.show() + "\n"        
        return res
    
    def showTeams(self, showStatuses = False):
        return [team.showUnits(showStatuses) for team in self.teams]


    def __calculateTurnOrder(self):
        res = ((unit, i, j) for i, team in enumerate(self.teams) for j, unit in enumerate(team.units) if unit.acts > 0)
        if len(res) > 0: return min(res, key = lambda x : (-x(0).turnPriority, x(1), x(2)))[0]
        else: return None
    

# =============================================================================
# Players & AI
# =============================================================================

class Player(DelObj):
    
    def __init__(self, session):
        super().__init__(self)
        self.units = []
        self.session = session
    
    async def turnCycle(self, unit):
        if unit not in self.units: return
        
    async def onQuickEffectCycle(self, unit, **keywargs):
        pass
        

class AI(DelObj):
    
    def __init__(self, session, code):
        super().__init__(self)
        self.units = []
        self.session = session
    
    async def turnCycle(self, unit):
        if unit not in self.units: return
        return self.code()
        
    async def onQuickEffectCycle(self, unit, **keywargs):
        pass
        
        