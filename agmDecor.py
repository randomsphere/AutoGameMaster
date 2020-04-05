
from functools import wraps

# =============================================================================
# Event Decors
# =============================================================================

def EvMethod(evholder, ev, order=0, on_unit=True):

    def real_wrapper(func):

        @wraps(func)
        def pseudo_wrapper(self, *args, **kwargs):
            pseudo_wrapper.EV    = ev
            pseudo_wrapper.ORDER = order
            pseudo_wrapper.ON_UNIT = on_unit

            if not all(c(*args, **kwargs) for c in self.conditions): return
            func(self, *args, **kwargs)

        return pseudo_wrapper

    evholder._events.add(real_wrapper)
    return real_wrapper

def EvStart(func):

    @wraps(func)
    def wrapper(self):
        if self.isEvsOn: return

        for ev in self._events:
            target = None
            if ev.ON_UNIT: target = self.unit
            else: target = self.unit.team.st

            if not target.isDeleted(): target.addEvent(event)

        func()

    return wrapper

def EvStop(func):

    @wraps(func)
    def wrapper(self):
        if not self.isEvsOn: return

        for ev in self._events:
            target = None
            if ev.ON_UNIT:
                if self.unit != None: target = self.unit
            else: target = self.unit.team.st

            if target.isDeleted(): continue
            target.revEvent(event)

        func()

    return wrapper

# =============================================================================
# Status Tickers
# =============================================================================

def StatusTicker(func):

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        res = func(*args, **kwargs)
        if res:
            if self.turns != None:
                self.turns-=1
                if self.turns == 0:
                    self.remove()
                    self.delete()

    return wrapper


def StatusConsumer(func):

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        res = func(*args, **kwargs)
        if res:
            if self.uses != None:
                self.uses-=1
                if self.uses == 0:
                    self.remove()
                    self.delete()

    return wrapper

# =============================================================================
# Command .use() Decors
# =============================================================================

def CommandQE(func):

    @wraps(func)
    async def wrapper(self, embedMenu):
        if embedMenu == None return False
        return func(self, embedMenu)

def CommandRestrict(func):

    @wraps(func)
    async def wrapper(self, embedMenu):
        if not (self.isUsable() and self.commandtype.isUsable()): return False
        if self.cd > 0: return False
        return func(self, embedMenu)

    return wrapper

def CommandCooldown(func):

    @wraps(func)
    async def wrapper(self, embedMenu):
        self.cd = self.maxcd
        return func(self, embedMenu)

    return func

def CommandHold(func):

    @wraps(func)
    async def wrapper(self, embedMenu):
        self.cd = -1
        return func(self, embedMenu)

    return wrapper

def CommandUse(func):

    @wraps(func)
    async def wrapper(self, embedMenu):

        await self.action.define(self.commandtype.unit, embedMenu)

        await self.commandtype.unit.callEvent("action",
                            self.action, type(self.commandtype))

        if not await self.action.execute(self.commandtype.unit): return False

        return func(self, embedMenu)

    return wrapper

# =============================================================================
# Action Creator Decor
# =============================================================================

def addMethod(cls, func):

    def wrapper(self, *args, **kwargs):
        return func(*args, **kwargs)

    setattr(cls, func.__name__, wrapper)

def ActionCreator(name, desc='', cd=None, actionWrapper=WrappedAction):

    @wraps(func)
    def wrapper(func):

        def pseudo_wrapper():
            listFuncs = func(); action = Action()
            addMethod(cls, listFuncs.pop()); addMethod(cls, listFuncs.pop())

            res = actionWrapper(name, desc, action, cd)
            for m in listFuncs: addMethod(res, m)

            return res

        return pseudo_wrapper

    return wrapper

def PassiveCreator(name, desc='', passiveWrapper=Command):

    @wraps(func)
    def wrapper(func):

        def pseudo_wrapper():
            listFuncs = func(); action = Action()
            addMethod(cls, listFuncs.pop()); addMethod(cls, listFuncs.pop())

            res = actionWrapper(name, desc, action, cd)
            for m in listFuncs: addMethod(res, m)

            return res

        return pseudo_wrapper

    return wrapper

def PlayerTakeTurn(func):

    @wraps(func)
    async def takeTurn(self, unit, tick=False):

        unit.acts = 1

        unit.callEventAll('init_unit_turn', unit)
        if tick: unit.callEventAll('tick', unit)

        if unit.acts < 1: return False

        while unit.acts > 0:
            pass

        return True

    return func
