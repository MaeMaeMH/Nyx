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
        
        self.YTDL_OPTIONS = {'format': 'bestaudio', 'nonplaylist': 'True'}
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
            }
        
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
            
    async def join_VC(self, ctx, channel):
        """
        Connects the bot to the specified voice channel or moves it if already connected.

        Checks if the bot is already connected to a voice channel in the current guild:
        - If the bot is not connected, it attempts to connect to the provided channel.
        - If the connection fails, an error message is sent to the context.
        - If the bot is already connected to a voice channel, it moves to the provided channel.

        Parameters:
            ctx (Context): The context from the command invocation, containing guild info.
            channel (VoiceChannel): The target voice channel to which the bot should join or move.

        Returns:
            None
        """
        id = int(ctx.guild.id)
        if self.vc[id] == None or not self.vc[id].is_connected():
            self.vc[id] = await channel.connect()

            if self.vc[id] == None:
                await ctx.send("Could not connect to the voice channel.")
                return
        else:
            await self.vc[id].move_to(channel)
            
    def search_YT(self, search):
        """
        Searches YouTube for the given query and returns the top 10 video IDs.

        This method constructs a search query string, performs the search on YouTube, 
        and extracts the video IDs from the search results. It returns a list of the 
        top 10 video IDs found.

        Parameters:
            search (str): The search query to look up on YouTube.

        Returns:
            list: A list of up to 10 YouTube video IDs (strings).
        """
        queryString = parse.urlencode({'search_query': search})
        htmContent = request.urlopen('http://www.youtube.com/results?' + queryString)
        searchResults = re.findall('/watch\?v=(.{11})', htmContent.read().decode())
        return searchResults[0:10]