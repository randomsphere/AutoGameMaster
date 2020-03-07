import commands
import discord
from agm import *
import re
from react_msg import ReactMsg

import asyncio
import nest_asyncio
nest_asyncio.apply()

SESSIONS = {}


@commands.command(condition=lambda line : commands.first_arg_match(line, 'agm'))
async def c_autogm(line, message, bot=discord.Client()):
    args = line.split(" ")[1:]
    argslen = len(args)
    
    if argslen == 1:
        if args[0] == "start":
            SESSIONS[message.user.id] = Session(message.channel)
            return "Session inicialized."
        if args[0] == "close":
            SESSIONS[message.user.id] = None
            return "Session ended."
        if args[0] == "stop":
            await SESSIONS[message.user.id].toggleHaltCycle()
    
    elif argslen >= 3:
        if args[0] == "add":
            if args[1] == "player":
                pass
    
    else:
        return "**[Error]** AutoGameMaster commands require at least one argument."


class Session:
    
    def __init__(self, channel):
        self.players      = []
        self.battlefield  = Battlefield(self)
        self.channel      = channel
        self.isRunning    = True
    
    async def toggleHaltCycle(self):
        if not self.isRunning: 
            self.isRunning = True
            return 
        
        self.isRunning = False
        