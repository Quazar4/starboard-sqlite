import discord
from discord.ext import commands
import aiosqlite

class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def create_starboard_table(self):
        async with aiosqlite.connect('starboard.db') as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS starboard (
                    message_id INTEGER PRIMARY KEY,
                    starboard_message_id INTEGER,
                    star_count INTEGER
                )
            ''')
            await db.commit()

    @commands.Cog.listener()
    async def on_ready(self):
        print('Starboard cog is ready!')
        await self.create_starboard_table()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if str(payload.emoji) == '⭐' and not payload.member.bot:
            async with aiosqlite.connect('starboard.db') as db:
                cursor = await db.execute('SELECT * FROM starboard WHERE message_id = ?', (payload.message_id,))
                starboard_entry = await cursor.fetchone()

                if not starboard_entry:
                    channel = self.bot.get_channel(payload.channel_id)
                    message = await channel.fetch_message(payload.message_id)

                    starboard_channel = discord.utils.get(channel.guild.text_channels, name='starboard')
                    if not starboard_channel:
                        starboard_channel = await channel.guild.create_text_channel('starboard')

                    starboard_message = await starboard_channel.send(
                        f'Stars: {payload.count} {message.jump_url}'
                    )

                    await db.execute(
                        'INSERT INTO starboard (message_id, starboard_message_id, star_count) VALUES (?, ?, ?)',
                        (payload.message_id, starboard_message.id, payload.count)
                    )
                    await db.commit()
                else:
                    star_count = starboard_entry[2] + 1
                    starboard_channel = discord.utils.get(payload.member.guild.text_channels, name='starboard')
                    if starboard_channel:
                        starboard_message = await starboard_channel.fetch_message(starboard_entry[1])
                        await starboard_message.edit(content=f'Stars: {star_count} {starboard_message.jump_url}')

                    await db.execute(
                        'UPDATE starboard SET star_count = ? WHERE message_id = ?',
                        (star_count, payload.message_id)
                    )
                    await db.commit()

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if str(payload.emoji) == '⭐':
            async with aiosqlite.connect('starboard.db') as db:
                cursor = await db.execute('SELECT * FROM starboard WHERE message_id = ?', (payload.message_id,))
                starboard_entry = await cursor.fetchone()

                if starboard_entry:
                    star_count = starboard_entry[2] - 1
                    starboard_channel = discord.utils.get(self.bot.fetch_guild(payload.guild_id).text_channels, name='starboard')
                    if starboard_channel:
                        starboard_message = await starboard_channel.fetch_message(starboard_entry[1])
                        await starboard_message.edit(content=f'Stars: {star_count} {starboard_message.jump_url}')

                    if star_count <= 0:
                        await db.execute('DELETE FROM starboard WHERE message_id = ?', (payload.message_id,))
                    else:
                        await db.execute(
                            'UPDATE starboard SET star_count = ? WHERE message_id = ?',
                            (star_count, payload.message_id)
                        )
                    await db.commit()

    @commands.command()
    async def starboard(self, ctx, message_id: int):
        async with aiosqlite.connect('starboard.db') as db:
            cursor = await db.execute('SELECT * FROM starboard WHERE message_id = ?', (message_id,))
            starboard_entry = await cursor.fetchone()

            if starboard_entry:
                starboard_channel = discord.utils.get(ctx.guild.text_channels, name='starboard')
                if starboard_channel:
                    starboard_message = await starboard_channel.fetch_message(starboard_entry[1])
                    await ctx.send(f'This message has {starboard_entry[2]} stars: {starboard_message.jump_url}')
            else:
                await ctx.send('This message has no stars.')

def setup(bot):
    bot.add_cog(Starboard(bot))
