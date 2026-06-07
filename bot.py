import discord
from discord.ext import commands
from discord.ui import Button, View
from datetime import timedelta
from collections import defaultdict
import asyncio
import os

# =====================
# CONFIG (RAILWAY)
# =====================
TOKEN = os.getenv("TOKEN")

AUTO_ROLE_ID = 1510649141980692571
LOG_CHANNEL_ID = 1510650271863148595
TICKET_CATEGORY_ID = 1513170797672530111
TICKET_PANEL_CHANNEL_ID = 1510650224916566137

MOD_ROLE_ID = 1510649113023086666
ADMIN_ROLE_ID = 1510649108623524023
OWNER_ROLE_ID = 1510649101832818790

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

spam = defaultdict(list)

# =====================
# PERMISSIONS
# =====================
def has_role(member, role_id):
    return any(r.id == role_id for r in member.roles)

def owner(m): return has_role(m, OWNER_ROLE_ID)
def admin(m): return owner(m) or has_role(m, ADMIN_ROLE_ID)
def mod(m): return admin(m) or has_role(m, MOD_ROLE_ID)

# =====================
# LOGS
# =====================
async def log(guild, title, desc, color=discord.Color.blue()):
    ch = guild.get_channel(LOG_CHANNEL_ID)
    if ch:
        embed = discord.Embed(title=title, description=desc, color=color)
        await ch.send(embed=embed)

# =====================
# READY
# =====================
@bot.event
async def on_ready():
    print(f"✅ {bot.user}")

    ch = bot.get_channel(TICKET_PANEL_CHANNEL_ID)
    if ch:
        await ch.purge(limit=10)
        await ch.send("🎫 Tickets", view=TicketView())

# =====================
# JOIN / ROLE
# =====================
@bot.event
async def on_member_join(member):
    role = member.guild.get_role(AUTO_ROLE_ID)
    if role:
        await member.add_roles(role)
    await log(member.guild, "Join", str(member), discord.Color.green())

# =====================
# LOG MESSAGES
# =====================
@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    await log(message.guild, "Delete", f"{message.author}: {message.content}", discord.Color.orange())

@bot.event
async def on_message_edit(before, after):
    if before.author.bot:
        return
    await log(before.guild, "Edit", f"{before.content} ➜ {after.content}", discord.Color.yellow())

# =====================
# ANTI SPAM + ANTI INVITE
# =====================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if not owner(message.author):
        if "discord.gg/" in message.content:
            await message.delete()
            return

        now = asyncio.get_event_loop().time()
        spam[message.author.id].append(now)
        spam[message.author.id] = [t for t in spam[message.author.id] if now - t < 5]

        if len(spam[message.author.id]) >= 6:
            try:
                await message.author.timeout(timedelta(minutes=5))
            except:
                pass
            await message.channel.send(f"🔇 {message.author.mention} mute anti-spam")
            return

    await bot.process_commands(message)

# =====================
# TICKETS (BUTTON)
# =====================
class Close(Button):
    def __init__(self):
        super().__init__(label="Fermer", style=discord.ButtonStyle.red)

    async def callback(self, interaction):
        await interaction.response.send_message("Fermeture...", ephemeral=True)
        await asyncio.sleep(2)
        await interaction.channel.delete()

class Ticket(Button):
    def __init__(self):
        super().__init__(label="Créer ticket", style=discord.ButtonStyle.green)

    async def callback(self, interaction):
        guild = interaction.guild
        user = interaction.user

        category = guild.get_channel(TICKET_CATEGORY_ID)

        ch = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            category=category
        )

        await ch.set_permissions(user, read_messages=True, send_messages=True)
        await ch.set_permissions(guild.default_role, read_messages=False)

        view = View()
        view.add_item(Close())

        embed = discord.Embed(
            title="🎫 Ticket",
            description="Explique ton problème",
            color=discord.Color.green()
        )

        await ch.send(user.mention, embed=embed, view=view)
        await interaction.response.send_message(f"Ticket créé {ch.mention}", ephemeral=True)

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Ticket())

# =====================
# COMMANDES
# =====================
@bot.command()
async def kick(ctx, member: discord.Member):
    if not mod(ctx.author): return
    await member.kick()

@bot.command()
async def ban(ctx, member: discord.Member):
    if not admin(ctx.author): return
    await member.ban()

@bot.command()
async def clear(ctx, amount: int):
    if not mod(ctx.author): return
    await ctx.channel.purge(limit=amount)

@bot.command()
async def mute(ctx, member: discord.Member, minutes: int):
    if not mod(ctx.author): return
    await member.timeout(timedelta(minutes=minutes))

@bot.command()
async def giverole(ctx, member: discord.Member, role: discord.Role):
    if not admin(ctx.author): return
    await member.add_roles(role)

@bot.command()
async def say(ctx, *, msg):
    if not mod(ctx.author): return
    await ctx.message.delete()
    await ctx.send(msg)

bot.run(TOKEN)
