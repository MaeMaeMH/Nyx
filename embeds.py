import discord

class BaseEmbed(discord.Embed):
    def __init__(self, title="", description="", colour=0x1a1a40):
        super().__init__(title=title, description=description, colour=colour)
        self.set_footer(text="Nyx Music Bot - by MaeMaeMH")

class NowPlayingEmbed(BaseEmbed):
    def __init__(self, song, author):
        super().__init__(
            title="Now Playing",
            description=f"[{song['title']}]({song['link']})",
            colour=0x3b1a6b
        )
        self.set_thumbnail(url=song['thumbnail'])
        self.set_footer(text=f"Song added by: {str(author)}", icon_url=author.avatar_url)

class QueueEmbed(BaseEmbed):
    def __init__(self, queue: list):
        if not queue:
            desc = "The queue is currently empty."
        else:
            desc = "\n".join(
                [f"**{i+1}.** [{song['title']}]({song['link']})" for i, song in enumerate(queue)]
            )
        super().__init__(title="Current Queue", description=desc, colour=0x5a2d8b)
