import discord
from discord_components import Select, SelectOption, Button
from discord.ext import commands
import asyncio
from asyncio import run_coroutine_threadsafe
from urllib import parse, request
import re
import json
import os
from youtube_dl import YoutubeDL

class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.is_playing = {}
        self.is_paused = {}
        self.musicQueue = {}
        self.queueIndex = {}
        
        self.vc = {}
        
    @commands.Cog.listener()
    async def on_ready(self):
        """
        Event listener triggered when the bot has successfully connected to Discord and is ready.

        Initializes music-related data structures for each guild the bot is part of:
        - Creates an empty music queue for each guild.
        - Sets the initial queue index to 0.
        - Initializes the voice client reference to None.
        - Marks both 'is_paused' and 'is_playing' as False.

        This ensures that all guild-specific playback states are properly reset on bot startup.
        """
        for guild in self.bot.guilds:
            id = int(guild.id)
            self.musicQueue[id] = {}
            self.queueIndex[id] = 0
            self.vc[id] = None
            self.is_paused[id] = self.is_playing[id] = False