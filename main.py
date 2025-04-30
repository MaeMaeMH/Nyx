from discord_components import ComponentsBot
import os
from dotenv import load_dotenv
from music_cog import music_cog

bot = ComponentsBot(command_prefix='?')

bot.add_cog(music_cog(bot))

load_dotenv()
TOKEN = os.getenv('discord_token')
print("Rise my glorious creature!")
bot.run(TOKEN)
