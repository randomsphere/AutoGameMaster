# -*- coding: UTF-8 -*-
import discord
import asyncio


class ReactMsg:

    def __init__(self, userId, chnId, bot):
        self.userId = userId
        self.chnId = chnId
        self.bot = bot

        self.startMessage = startMessage
        self.defaultMessage = defaultMessage

        self.ctxList = []


    def fetchUser(self):
        return self.bot.get_user(self.userId)

    def fetchChannel(self):
        return self.bot.get_channel(self.chnId)

    async def fetchCtx(self, ctx=None, index=-1):
        x = None
        if index > -1:
            x = await self.fetchChannel().fetch_message(self.ctxList[index])
        elif ctx != None:
            x = await self.fetchChannel().fetch_message(ctx)
        return None


    async def editCtx(self, ctx=None, msg=None, embed=None, reactions=[], startMessage = "Message Loading!"):

        CTX = await self.fetchCtx(ctx)

        if CTX == None:
            ctx = (await self.fetchChannel().send(startMessage)).id
            self.ctxList.append(ctx)
            CTX = self.fetchCtx(ctx)

        if reactions == None:
            if CTX.channel != discord.DMChannel:
                await CTX.clear_reactions()
        else:
            for r in reactions:
                await CTX.add_reaction(r)

        if not (msg==None and embed==None):
            await CTX.edit(msg=msg, embed=embed)

        return CTX.id


    async def awaitReaction(self, reactions, ctxList=self.ctxList, timeout=None):
        try:
            return await (self.bot.wait_for('reaction_add', timeout=timeout,
                            check = lambda reaction, user: user.id == self.userId and reaction.message.id in self.ctxList and str(reaction) in reactions)).emoji
        except asyncio.TimeoutError:
            return None

    async def awaitMessage(self):
        try:
            return (await self.bot.wait_for('message', timeout=timeout,
                    check=lambda ctx: return ctx.author.id == self.userId and ctx.channel.id == self.chnId)).content
        except asyncio.TimeoutError:
            return None



class MenuMsg(ReactMsg):

    def __init__(self, userId, chnId, bot):
        super().__init__(userId, chnId, bot)

    async def genericOptionMenu(self, selectCountMax=1):

        if selectCountMax < 1: return None

        RES = []

        while len(RES) < selectCountMax:
            pass


    async def genericOptionMenu(self, options, selectCountMax = 1):

        embed.add_field(name="", value="")

        lenOp = len(options)

        i  = 0
        RES = []

        while len(RES) < selectCountMax:

            # Draw Embed
            valueText  = ""
            for index in range(i-2, i+3):
                optionText = ""
                if 0 <= index < lenOp: optionText = options[index].getName()

                if index != i: optionText = "-" + optionText
                else: optionText = ">" + optionText + "<"

                valueText += optionText + "\n"

            embed.set_field_at(1, name=f"< {options[j].getTitle()} >",
                            value=valueText + "\n" + option1D[i].getDesc(),
                            inline=False)


            # Obtain Input
            res = await self.update(embed=embed, reactions=["⬅️","⬆️","✅", "🚫", "⬇️","➡️"])


            # Change value depending on Input
            if res == "🚫":
                try: RES.pop()
                except IndexError: return None

            elif res == "✅":
                selectCount -= 1
                RES.append(option1D[i])

            else:
                if res == "⬅️":  j = (j + lenOp-1)%lenOp
                elif res == "➡️": j = (j + 1)%lenOp
                else:
                    if res == "⬆️": i = (i+lenOp1D-1)%lenOp1D
                    if res == "⬇️": i = (i+1)%lenOp1D


        return RES if len(RES) > 1 else RES[0]
'''
