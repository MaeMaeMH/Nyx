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
        
        self.embedBlue = 0x2c76dd
        self.embedRed = 0xdf1141
        self.embedGreen = 0x0eaa51
        
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
   
    def now_playing_embed(self, ctx, song):
            title = song['title']
            link = song['link']
            thumbnail = song['thumbnail']
            author = ctx.author
            avatar = author.avatar_url
            
            embed = discord.Embed(
                title="Now Playing",
                description=f'[{title}]({link})',
                colour=self.embedBlue
            )
            embed.set_thumbnail(url=thumbnail)
            embed.set_footer(text=f'Song added by: {str(author)}', icon_url=avatar)
            return embed
            
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
        print(f"[DEBUG] join_VC called for guild {id}")

        try:
            if self.vc.get(id) is None or not self.vc[id].is_connected():
                print("[DEBUG] Attempting to connect...")
                self.vc[id] = await channel.connect() #! Port need to be open for the bot to return. Currently it gets stuck here and never returns
                print("[DEBUG] Connected.")
            else:
                print("[DEBUG] Moving to new channel...")
                await self.vc[id].move_to(channel)
                print("[DEBUG] Moved.")
        except Exception as e:
            print(f"[ERROR] join_VC failed: {e}")
            raise
            
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
    
    def extract_YT(self, url):
        """
        Extracts YouTube video information such as title, thumbnail, and video URL.

        This method uses `youtube-dl` to extract video details without downloading the video. 
        It retrieves information such as the video title, the source URL of the video, 
        and the thumbnail image URL.

        Parameters:
            url (str): The URL of the YouTube video to extract information from.

        Returns:
            dict: A dictionary containing the video title, video URL, thumbnail URL, and the source URL of the video.
                Returns False if there was an error during extraction.
        """
        with YoutubeDL(self.YTDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except:
                return False
        return {
            'link': 'https://www.youtube.com/watch?v=' + url,
            'thumbnail': 'https://i.ytimg.com/vi/' + url + '/hqdefault.jpg?sqp=-oaymwEcCOADEI4CSFXyq4qpAw4IARUAAIhCGAFwAcABBg==&rs=AOn4CLD5uL4xKN-IUfez6KIW_j5y70mlig',
            'source': info['formats'][0]['url'],
            'title': info['title']
        }
        
    def play_next(self, ctx):
        """
        Plays the next song in the queue or stops playback if the queue has ended.

        This method is used as a callback when a song finishes playing. It:
        - Verifies that playback is active for the current guild.
        - Checks if another song is available in the queue.
            - If yes: increments the queue index, retrieves the next song, sends a message, and plays it.
            - If no: advances the queue index and stops playback.
        - Uses `run_coroutine_threadsafe` to safely send a message from a non-async context.
        - Registers itself again as the callback after the new song finishes.

        Parameters:
            ctx (Context): The context object associated with the guild.

        Returns:
            None
        """
        id = id(ctx.guild.id)
        if not self.is_playing[id]:
            return
        if self.queueIndex[id] + 1 < len(self.musicQueue[id]):
            self.is_playing[id] = True
            self.queueIndex[id] += 1
            
            song = self.musicQueue[id][self.queueIndex[id][0]]
            message = self.now_playing_embed(ctx, song)
            coroutine = ctx.send(embed=message)
            fut = run_coroutine_threadsafe(coroutine, self.bot.loop)
            try:
                fut.result()
            except:
                pass
            
            self.vc[id].play(discord.FFmpegPCMAudio(
                song['source'], **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
        else:
            self.queueIndex[id] += 1
            self.is_playing[id] = False
        
    async def play_music(self, ctx):
        """
        Plays the next song in the queue for the current guild or sends a message if the queue is empty.

        Checks if the current queue index is within the queue bounds. If so:
        - Marks the bot as playing and not paused.
        - Joins the appropriate voice channel from the queued song entry.
        - Retrieves the song data and sends a message to the text channel (placeholder for now).
        - Begins audio playback using FFmpeg with the configured options.
        - Sets a callback to continue with the next song when playback finishes.

        Parameters:
            ctx (Context): The context of the command invocation, used for guild and channel resolution.

        Returns:
            None
        """
        id = int(ctx.guild.id)
        if self.queueIndex[id] < len(self.musicQueue[id]):
            self.is_playing[id] = True
            self.is_paused[id] = False
                
            await self.join_VC(ctx, self.musicQueue[id][self.queueIndex[id][1]])

            song = self.musicQueue[id][self.queueIndex[id]][0]
            message = self.now_playing_embed(ctx, song)
            await ctx.send(embed=message)
            
            self.vc[id].play(discord.FFmpegPCMAudio(
                song['song'], **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
        else:
            await ctx.send("There are no songs in the queue to be played.")
            self.queueIndex[id] += 1
            self.is_playing = False #! Unsure if a an '[id]' is needed after self.is_playing or not, revisit later!
    
    @ commands.command(
        name="join",
        aliases=["j"],
        help=""
    )
    async def join(self, ctx):
        if ctx.author.voice:
            userChannel = ctx.author.voice.channel
            try:
                print("✅ join_VC abgeschlossen")
                await ctx.send(f'Nyx has joined {userChannel}')
                await self.join_VC(ctx, userChannel)
                await ctx.send(f'Wo bleibt der Rest???')
            except Exception as e:
                print(f"❌ Fehler in join_VC: {e}")
                await ctx.send(f"Fehler beim Beitreten des Channels: {e}")
        else:
            await ctx.send("You need to be connected to a voice channel.")

    @ commands.command(
        name="leave",
        aliases=["l"],
        help=""
    )  
    async def leave(self, ctx):
        print("Funtion called")
        id = int(ctx.guild.id)
        self.is_playing[id] = self.is_paused[id] = False
        self.musicQueue[id] = []
        self.queueIndex[id] = 0
        if self.vc[id] != None:
            await ctx.send("Nyx has left the channel")
            await self.vc[id].disconnect()
        else:
            print("Not leaving bitch")
            print(self.vc[id])