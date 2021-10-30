import discord
import requests

from chat_exporter.build_html import (
    fill_out, embed_body, embed_title, embed_description, embed_field,
    embed_field_inline, embed_footer, embed_footer_icon, embed_image,
    embed_video, embed_thumbnail, embed_author, embed_author_icon,
    PARSE_MODE_EMBED, PARSE_MODE_SPECIAL_EMBED, PARSE_MODE_NONE,
    PARSE_MODE_MARKDOWN
)

def url_rewrite(url):
    # rewrite common bad resource links to point to the right thing
    if "//imgur.com/" in url:
        url = url.replace("imgur", "i.imgur")
        if not ".png" in url:
            url = url + ".png"
    return url

def local_download(url, directory, embed_id, attribute):
    """
    Downloads a resource from given url to filename.

    Returns True iff a file was successfully downloaded.
    """
    #TODO better url interpret logic
    url = url_rewrite(url)
    #TODO better way to figure out file extension than from url / embed types
    #TODO assumes filename opening / writing succeeds
    extensions = [
        ("thumbnail",".png"),
        (".gif",".gif"),
        ("png",".png"),
        ("mp4",".mp4"),
        ("/mp4",".mp4"),
        (".png",".png"),
        (".mp4",".mp4"),
    ]
    extension = ".html" # fallback extension
    for e,ext in extensions:
        if e in url:
            extension = ext
    file = open(directory + embed_id + attribute + extension, 'wb')
    response = requests.get(url, stream=True)
    try:
        response = requests.get(url, stream=True)
    except Exception:
        #TODO assumes downloading is reasonably quick / no conn problems
        # could do retry attempts / more robust stuff
        file.close()
        return False
    
    if not response.ok:
        file.close()
        return False
    
    for block in response.iter_content(1024):
        if not block:
            break
        file.write(block)
    file.close()
    return (embed_id + attribute + extension)

    
def download_embeds(embed, directory, embed_id):
    # download all possible embed resources
    # TODO: use embed type to find which ones to dowload instead of trying all
    # types: rich, image, video, gifv, article, link
    # (problem embed.type might not be set or devs use lazy .url value)
    # https://discord.com/developers/docs/resources/channel#embed-object-embed-types

    # likely the main resource if a lazy dev only set this
    if embed.url != discord.Embed.Empty:
        embed.url = local_download(
            embed.url,
            directory, embed_id, "_url"
        )
    # image: url, proxy_url, height, width
    if embed.image != discord.Embed.Empty:
        if embed.image.url != discord.Embed.Empty:
            embed._image["url"] = local_download(
                embed.image.url,
                directory, embed_id, "_image_url"
            )
    # video: url, proxy_url, height, width
    if embed.video != discord.Embed.Empty:
        if embed.video.url != discord.Embed.Empty:
            embed._video["url"] = local_download(
                embed.video.url,
                directory, embed_id, "_video_url"
            )
    # thumbnail: url, proxy_url, height, width
    if embed.thumbnail != discord.Embed.Empty:
        if embed.thumbnail.url != discord.Embed.Empty:
            embed._thumbnail["url"] = local_download(
                embed.thumbnail.url,
                directory, embed_id, "_thumbnail_url"
            )
    # footer: text, icon_url, proxy_icon url (not very interesting)
    if embed.footer != discord.Embed.Empty:
        if embed.footer.icon_url != discord.Embed.Empty:
            embed._footer["icon_url"] = local_download(
                embed.footer.icon_url,
                directory, embed_id, "_footer_icon_url"
            )
    # other possible resources
    # provider: name, url (skipped, most likely just a site link)
    # author: name, url, icon_url, proxy_icon_url
    # possibly in fields but highly unlikely

class BuildEmbed:
    r: str
    g: str
    b: str
    title: str
    description: str
    author: str
    image: str
    thumbnail: str
    footer: str
    fields: str

    def __init__(self, embed, guild, directory=None, embed_id=None):
        self.embed: discord.Embed = embed
        self.guild: discord.Guild = guild
        self.directory = directory
        self.embed_id = embed_id
        # Lazy check if local downloading expected
        if directory is not None:
            download_embeds(embed,directory, embed_id)

    async def flow(self):
        self.build_colour()
        await self.build_title()
        await self.build_description()
        await self.build_fields()
        await self.build_author()
        await self.build_thumbnail()
        await self.build_image()
        await self.build_video()
        await self.build_footer()
        await self.build_embed()

        return self.embed

    def build_colour(self):
        self.r, self.g, self.b = (self.embed.colour.r, self.embed.colour.g, self.embed.colour.b) \
            if self.embed.colour != discord.Embed.Empty \
            else (0x20, 0x22, 0x25)  # default colour

    async def build_title(self):
        self.title = self.embed.title \
            if self.embed.title != discord.Embed.Empty \
            else ""

        if self.title != "":
            self.title = await fill_out(self.guild, embed_title, [
                ("EMBED_TITLE", self.title, PARSE_MODE_MARKDOWN)
            ])

    async def build_description(self):
        self.description = self.embed.description \
            if self.embed.description != discord.Embed.Empty \
            else ""

        if self.description != "":
            self.description = await fill_out(self.guild, embed_description, [
                ("EMBED_DESC", self.embed.description, PARSE_MODE_EMBED)
            ])

    async def build_fields(self):
        self.fields = ""
        for field in self.embed.fields:
            if field.inline:
                self.fields += await fill_out(self.guild, embed_field_inline, [
                    ("FIELD_NAME", field.name, PARSE_MODE_SPECIAL_EMBED),
                    ("FIELD_VALUE", field.value, PARSE_MODE_EMBED)
                ])
            else:
                self.fields += await fill_out(self.guild, embed_field, [
                    ("FIELD_NAME", field.name, PARSE_MODE_SPECIAL_EMBED),
                    ("FIELD_VALUE", field.value, PARSE_MODE_EMBED)])

    async def build_author(self):
        self.author = self.embed.author.name \
            if self.embed.author.name != discord.Embed.Empty \
            else ""

        self.author = f'<a class="chatlog__embed-author-name-link" href="{self.embed.author.url}">{self.author}</a>' \
            if self.embed.author.url != discord.Embed.Empty \
            else self.author

        author_icon = await fill_out(self.guild, embed_author_icon, [
            ("AUTHOR", self.author, PARSE_MODE_NONE),
            ("AUTHOR_ICON", self.embed.author.icon_url, PARSE_MODE_NONE)
        ]) \
            if self.embed.author.icon_url != discord.Embed.Empty \
            else ""

        if author_icon == "" and self.author != "":
            self.author = await fill_out(self.guild, embed_author, [("AUTHOR", self.author, PARSE_MODE_NONE)])
        else:
            self.author = author_icon

    async def build_image(self):
        if self.embed.image.url != discord.Embed.Empty:
            self.image = await fill_out(
                self.guild,
                embed_image,
                [(
                    "EMBED_IMAGE",
                    str(self.embed.image.url),
                    PARSE_MODE_NONE
                )]
            )
            self.thumbnail = ""
        elif self.embed.type == "image":
            if self.embed.url != discord.Embed.Empty:
                self.image = await fill_out(
                    self.guild,
                    embed_image,
                    [(
                        "EMBED_IMAGE",
                        str(self.embed.url),
                        PARSE_MODE_NONE
                    )]
                )
            self.thumbnail = ""
        else:
            self.image = ""
    
    async def build_video(self):
        if self.embed.video.url != discord.Embed.Empty:
            self.video = await fill_out(
                self.guild,
                embed_video,
                [(
                    "EMBED_VIDEO",
                    str(self.embed.video.url),
                    PARSE_MODE_NONE
                )]
            )
            self.image = ""
            self.thumbnail = ""
        elif self.embed.type == "gifv" or self.embed.type == "video":
            if self.embed.url != discord.Embed.Empty:
                self.video = await fill_out(
                    self.guild,
                    embed_video,
                    [(
                        "EMBED_VIDEO",
                        str(self.embed.url),
                        PARSE_MODE_NONE
                    )]
                )
            self.image = ""
            self.thumbnail = ""
        else:
            self.video = ""

    async def build_thumbnail(self):
        if self.embed.thumbnail.url != discord.Embed.Empty:
            self.thumbnail = await fill_out(
                self.guild,
                embed_thumbnail,
                [(
                    "EMBED_THUMBNAIL",
                    str(self.embed.thumbnail.url),
                    PARSE_MODE_NONE
                )]
            )
        else:
            self.thumbnail = ""

    async def build_footer(self):
        footer = self.embed.footer.text \
            if self.embed.footer.text != discord.Embed.Empty \
            else ""
        footer_icon = self.embed.footer.icon_url \
            if self.embed.footer.icon_url != discord.Embed.Empty \
            else None

        if footer != "":
            if footer_icon is not None:
                self.footer = await fill_out(self.guild, embed_footer_icon, [
                    ("EMBED_FOOTER", footer, PARSE_MODE_NONE),
                    ("EMBED_FOOTER_ICON", footer_icon, PARSE_MODE_NONE)
                ])
            else:
                self.footer = await fill_out(self.guild, embed_footer, [
                    ("EMBED_FOOTER", footer, PARSE_MODE_NONE),
                ])
        else:
            self.footer = ""

    async def build_embed(self):
        self.embed = await fill_out(self.guild, embed_body, [
            ("EMBED_R", str(self.r)),
            ("EMBED_G", str(self.g)),
            ("EMBED_B", str(self.b)),
            ("EMBED_AUTHOR", self.author, PARSE_MODE_NONE),
            ("EMBED_TITLE", self.title, PARSE_MODE_NONE),
            ("EMBED_IMAGE", self.image, PARSE_MODE_NONE),
            ("EMBED_VIDEO", self.video, PARSE_MODE_NONE),
            ("EMBED_THUMBNAIL", self.thumbnail, PARSE_MODE_NONE),
            ("EMBED_DESC", self.description, PARSE_MODE_NONE),
            ("EMBED_FIELDS", self.fields, PARSE_MODE_NONE),
            ("EMBED_FOOTER", self.footer, PARSE_MODE_NONE)
        ])
