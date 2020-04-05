# -*- coding: utf-8 -*-
from AutoGameMaster.reactMsg import ReactMsg
import AutoGameMaster.agmDecor

from collections import defaultdict, OrderedDict
import discord
import math
import functools
import asyncio

# =============================================================================
# DelObj
# =============================================================================



class DelObj:

    def __init__(self):
        self.__isdel = False

    def isDeleted(self):
        return self.__isdel

    def delete(self):
        self.__isdel = True



# =============================================================================
# Fundamental Units
# =============================================================================



class EvCaller(DelObj):

    def __init__(self):
        self.__eventhandlers = defaultdict(set)

    def addEvent(self, handler):
        self.__eventhandlers[handler.EV].add(handler)
        return self

    def revEvent(self, handler):
        self.__eventhandlers[handler.EV].remove(handler)
        if (len(self.__eventhandlers[handler.EV]) is 0): del self.__eventhandlers[handler.EV]
        return self

    async def callEvent(self, event, *args, **keywargs):
        for eventhandler in sorted(self.__eventhandlers[event], key = lambda x : x.ORDER):
            await eventhandler(*args, **keywargs)
        return self


class EvHolder(DelObj):

    def __init__(self):
        super().__init__()
        self.unit       = None
        self.isEvsOn    = False
        self.conditions = set()
        self._events    = set()

    def setUnit(self, unit):
        self.unit = unit
        return self

    @agmDecor.EvStart()
    def start(self):
        ...

    @agmDecor.EvStop()
    def stop(self):
        ...


class Target(DelObj):

    def __init__(self, targets=None, priority_enabled=True, exceptions={}):
        self.targets    = targets
        self.priority   = priority_enabled
        self.exceptions = exceptions

    def __str__(self):
        if type(self.targets) == list:
            res = ""
            for t in self.targets:
                if t.isDeleted(): self.exceptions.remove(t)
                else: res += t.NAME + "&"
            return res[:-1]

        elif type(self.targets) == Team:
            res = "All " + self.targets.name
            if len(self.exceptions) > 0:
                res += " but "
                for t in self.exceptions:
                    if t.isDeleted(): self.exceptions.remove(t)
                    else: res += t.NAME + "&"
                return res[:-1]
            else:
                return res

        else: return ""

    def getContent(self):
        targets = self.targets if type(self.targets) == list else self.targets.units
        for unit in self.exceptions:
            try: targets.remove(unit)
            except ValueError : self.exceptions.remove(unit)
        return targets


class Action(DelObj):

    def __init__(self):
        super().__init__()
        self.vars = dict()



# =============================================================================
# Statuses
# =============================================================================



class Status(EvHolder):

    def __init__(self, isPerm = False, isVisible = True):
        super().__init__()
        self.isVisible = isVisible
        self.isPerm    = isPerm

        self.turns     = None
        self.uses      = None


    def __str__(self):
        return ""

    def getDesc(self):
        return ""


class MountStatus(Status):

    def __init__(self, isPerm = False, isVisible = True):
        super().__init__(self, isPerm, isVisible)
        self.riders = []


    def mountStatus(self, status, index=-1):

        status.conditions.extend(self.conditions)

        if index == -1: self.rider.append(status)
        else:           self.rider.insert(status,index)

        return self

    def dismountStatus(self,  index):
        status = self.rider[index]
        del self.rider[index]
        status.remove(self.conditions)

        return status



# =============================================================================
# Passives, Commands and Spells/Nonspells
# =============================================================================


class EventHolder(EvHolder):

    def __init__(self, name, desc):
        super().__init__()

        self.name = name
        self.desc = desc

    def getName(self):
        return self.name

    def getDesc(self):
        return self.desc


class WrappedAction(EventHolder):

    def __init__(self, name, desc, action, cd = None):
        super().__init__(name, desc)

        self.commandtype = None
        self.isAvailable = 0
        self.action      = action

        self.cd          = 0
        self.maxcd       = cd

    def setComType(self, comType):
        self.commandtype = comType
        return self

    def isUsable(self):
        return self.isAvailable == 0


    @agmDecor.EvMethod(self, 'turn')
    async def tick(self, *args, **kwargs):
        if self.cd > 0: self.cd = max(self.cd-1,0)

    @agmDecor.CommandRestrict()
    @agmDecor.CommandUse()
    async def use(self, embedMenu):
        pass


    def getName(self):
        res = self.name + (f'{self.cd if self.cd > 0 else ('R' if self.cd == 0 else "H")} ({str(self.maxcd)})') if self.maxcd != None else "")
        return (self.name if self.isUsable() else "*" + self.name + "* (BLOCKED)")

    def getDesc(self):
        return self.desc + ((f'Cooldown: {self.maxcd} turns') if self.maxcd != None else "")


class CastAction(WrappedAction):

    def __init__(self, name, desc, action, cd):
        super().__init__(name, desc, action, cd)

    @agmDecor.CommandRestrict()
    @agmDecor.CommandCooldown()
    @agmDecor.CommandUse()
    async def use(self, embedMenu):
        pass


class Passive(EventHolder):

    def __init__(self, name, desc):
        super().__init__(name, desc)


class CommandType(DelObj):

    def __init__(self, name, cmds=[]):
        super().__init__()

        self.unit        = None
        self.name        = name
        self.commands    = cmds
        self.isAvailable = 0


    def isUsable(self):
        return self.isAvailable == 0

    def getName(self):
        return self.name if self.isUsable() else "*" + self.name + "* (BLOCKED)"

    def getDesc(self):
        return ""

    def getContent(self):
        return self.commands

class NonspellType(CommandType):
    def __init__(self): super().__init__("Nonspells")

class SpellType(CommandType):
    def __init__(self): super().__init__("Spells")



# =============================================================================
# Unit Object
# =============================================================================

class Unit(EvCaller):

    def __init__(self):
        super().__init__()
        self.ROLE     = []
        self.NAME     = ''
        self.AP       = '1d20'
        self.GP       = '1d20'
        self.CP       = '5'

        self.turnPriority   = 0
        self.targetPriority = 0
        self.isGone         = 0

        self.acts           = 0

        self.owner     = None
        self.team      = None

        self.gauges    = OrderedDict()
        self.statuses  = set()
        self.passives  = []
        self.actions   = []


    # Event Stuff
    async def callEvent(self, event, *args, **keywargs):
        await super().callEvent(event, *args, **keywargs)

    async def callEventAll(self, event, *args, **keywargs):
        await super().callEvent(event, *args, **keywargs)
        await self.team.st.callEvent(event, *args, **keywargs)

    def start(self):
        for p in self.passives:
            p.start()

        for t in self.actions:
            for command in t.commands:
                command.start()

    def stop(self):
        for p in self.passives:
            p.stop()

        for t in self.actions:
            for command in t.commands:
                command.stop()


    # Extra Functionality
    def addToStatsheet(self, team, position=0):
        team.units.insert(position, self)
        self.team = team
        self.start()

    def removeFromStatsheet(self):
        self.stop()
        self.team.units.remove(self)
        self.team = None

    def getStatuses(self):
        per_stats = []
        nor_stats = []

        for status in self.statuses:
            if status.is_perm: per_stats.append(status)
            else:              nor_stats.append(status)
        return per_stats, nor_stats

    def isBanished(self):
        return self.isGone == 0


    # Print Functions
    def getTitle(self):
        res = ""
        if len(self.ROLE) > 0 : res +=  "[" + "/".join(self.ROLE) + "] "
        res += self.NAME
        if len(self.gauges) > 0: res += " - " + " / ".join(g.getName() for g in self.gauges)
        return res

    def getDesc(self):
        a,b = self.getStatuses()
        return "STATUSES: " + ("{" + ", ".join(s.getName() for s in a) + "}") if len(a) > 0 else "" + (", ".join(s.getName() for s in b) + ".") if len(b) > 0 else ""

# =============================================================================
# Team Object
# =============================================================================



class Team(DelObj):

    def __init__(self, name, statsheet):
        super().__init__()

        self.name        = name
        self.st          = statsheet

        self.units       = []
        self.patterns    = []
        self.gauges      = []


    def getTitle(self):
        return self.name

    def getDesc(self):
        return ""

    def getContent(self, targetPriority=False):
        if not targetPriority: return self.units
        else:
            units = defaultdict(list)
            for unit in self.units: units[unit.targetPriority].append(unit)
            return max(units.items())[1]



# =============================================================================
# Statsheet Object
# =============================================================================

class Statsheet(EvCaller):

    def __init__(self):
        super().__init__()

        self.turn     = None
        self.channel  = None

        self.name     = "Battlefield"
        self.teams    = [Team("Players", self), Team("Enemies", self)]


    # Printing Functions
    def showName(self):
        return self.name

    def showTeams(self, showStatuses = False):
        return [team.showUnits(showStatuses) for team in self.teams]

    async def showStatsheetEmbed(self, user, channel, bot):
        msg = ReactMsg(user, channel, bot)

        embed = discord.Embed(title=f"<< Test >>", description="")
        embed.add_field(name="<{ Controls }>", value="Use left and right to switch between different teams.\nUse up and down to shuffle between different units.\nUse ✅ or 🚫 to turn back.", inline=False)

        await msg.genericOption2DMenu(embed, 1, self.teams)


    #
    async def takeTurn(self, unit, tick=False):

        unit.acts = 1

        await unit.callEventAll('init_unit_turn', unit)
        if tick: await unit.callEvent('tick', unit)

        if unit.acts < 1: return

        await self.unit.owner.takeTurn(unit)


    # QE Event Awaiter
    async def awaitQE(self, qeType, timer=5):
        pass



# =============================================================================
# Players & AI
# =============================================================================

class Controller(DelObj):
    def __init__(self, sesh):
        super().__init__()
        self.sesh = sesh


class Player(Controller):

    def __init__(self, userId, bot, sesh):
        super().__init__(sesh)
        self.userId = userId
        self.bot  = bot

    def fetchUser(self):
        return self.bot.get_user(self.userId)


    async def takeTurn(self, unit, tick=False):

        i, j, j_rep = 0,0,0
        options = unit.getContent()
        controlEmbed = discord.Embed()

        msg = ReactMsg(self.userId, self.fetchUser().dm_channel, self.bot)
        mainCtx = await msg.editCtx(reactions=["🚫"], startMessage=f"{self.bot.get_user(self.userId).mention}'s turn!")
        await msg.editCtx(embed=controlEmbed, reactions=["⬅️","⬆️","✅", "⬇️","➡️"], startMessage="Please await warmly...")

        while unit.acts > 0:

            optionsLen = len(unit.commands)
            command = None

            while True:
                option    = unit.commands[i]
                optionLen = len(option)

                strDesc = ""
                for action in range(j_rep, j_rep+5):



                mainEmbed = discord.Embed(title=f"{self.unit.NAME}'s turn!'", description=f"({self.unit.actions} actions left)")
                mainEmbed.add_field(f"{option.name}", f"\`\`\`python\n{strDesc}\`\`\`", inline=False)

                await msg.editCtx(mainCtx, embed=mainEmbed)

                res = await msg.awaitReaction({"⬅️","⬆️","✅","⬇️","➡️"})
                if res == "✅":
                    command = unit.commands[i].actions[j]
                    break

                if res == "⬅️": i = (i+1)%optionsLen
                if res == "➡️": i = (i-1+optionsLen)%optionsLen
                if res == "⬇️": j = (j+1)%optionLen
                if res == "⬆️": j = (j-1+optionLen)%optionLen

                if j_rep > j: j_rep = j
                if j_rep+5 < j: j_rep = j-5

            if await command.use(msg): unit.acts -= 1
