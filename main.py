import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_reactions = True

bot = commands.Bot(command_prefix='!', intents=intents)

initial_extensions = [
    'cogs.starboard'
]

if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)

bot.run('TOKEN')
