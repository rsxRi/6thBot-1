from discord.ext import commands
from discord import Member, Embed
from typing import Optional
from random import choice
from asyncio import TimeoutError
from aiohttp import ClientSession
from json import loads
from re import sub


def get_lines(filename):
    with open(f"text/{filename}.txt", encoding="utf-8") as file:
        return file.readlines()


async def get_json_content(url):
    async with ClientSession() as session:
        async with session.get(url) as resp:
            print("Response:" + str(resp.status))
            json_string = await resp.text()
    return loads(json_string)


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.murder_lines: [str] = get_lines("kill")

    @commands.command()
    async def hug(self, ctx, target: Optional[Member] = None):
        # TODO Add hug counter
        you = ctx.author.display_name
        if target is None or target == ctx.author:
            await ctx.send(f"**{you}** hugs themselves. It makes them feel a little better.")
            return
        await ctx.send(f"**{you}** hugs **{target.display_name}**. It's a little awkward, but they don't mind.")

    @commands.command()
    async def kill(self, ctx, target: Optional[Member] = None):
        you: Member = ctx.author

        if target is None:
            await ctx.send(f"**{you.display_name}** wanted to murder someone, but never specified who.")
            return
        if target == ctx.author:
            await ctx.send(f"**{you.display_name}** needs to pick someone else, hmm?")
            return
        # Get from file (split by line), replace <you> and <user> with you and target respectively
        line = choice(self.murder_lines)
        line = line.replace("<you>", f"**{you.display_name}**")
        line = line.replace("<user>", f"**{target.display_name}**")
        print(line)
        await ctx.send(line)

    @commands.command()
    @commands.has_guild_permissions(manage_guild=True)
    async def lines(self, ctx):
        length = 0
        curr_msg = []
        for line in self.murder_lines:
            if len(line) + length < 2000:
                curr_msg.append(line)
                length += len(line)
            else:
                await ctx.send("".join(curr_msg))
                length = 0
                curr_msg = []
        if curr_msg is not []:
            await ctx.send("".join(curr_msg))

    async def get_gif(self, tags=None):
        url = f"http://api.giphy.com/v1/gifs/random?api_key={self.bot.giphy_api_key}&tag={tags}"
        return await get_json_content(url)

    @commands.command()
    @commands.cooldown(1, 60.0, type=commands.BucketType.member)
    async def gif(self, ctx, *, search: str = ""):
        """Posts a random gif from the tags you enter.

        gif --> completely random gif.
        gif [tags[]] --> narrows down the search to specific things.
        """
        content = await self.get_gif(search)
        data = content['data']

        if not data:
            em = Embed(title="Not Found 😕", description="We couldn't find a gif that matched the tags you entered.")
            await ctx.send(embed=em)
            return

        if search.strip() != "":
            search = sub(" +", ", ", search.strip())
            desc = f"🔎 Tags: **{search}**\n"
        else:
            desc = ""

        em = Embed(description="⌛ Loading Gif...")
        gif_msg = await ctx.send(embed=em)

        while True:
            size = int(data['images']['original']['mp4_size']) // 1024

            em = Embed(color=0xFA8072, description=f"{desc}[Original]({data['image_url']})")
            em.set_image(url=data['image_url'])
            em.set_footer(
                text=f"{data['image_width']}x{data['image_height']} | Frames: {data['image_frames']} | Size: {size}kb"
            )
            em.set_author(name=f"Requested by {str(ctx.author)}", icon_url=ctx.author.avatar_url)

            await gif_msg.edit(embed=em)
            await gif_msg.add_reaction('🔄')

            def check(msg_react, msg_user):
                return msg_user == ctx.author and msg_react.message.id == gif_msg.id and msg_react.emoji == '🔄'
            try:
                await self.bot.wait_for('reaction_add', timeout=15.0, check=check)
                print()
            except TimeoutError:
                print("Timed out")
                gif_msg = await ctx.channel.fetch_message(gif_msg.id)
                await gif_msg.clear_reaction('🔄')
                return

            await gif_msg.clear_reaction('🔄')
            content = await self.get_gif(search)
            data = content['data']


def setup(bot):
    bot.add_cog(Fun(bot))
