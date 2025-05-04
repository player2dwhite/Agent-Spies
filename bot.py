import discord
from discord.ext import commands, tasks
from discord.utils import get
from datetime import datetime, timedelta
import asyncio
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

server_count = 0
banned_users = {}
warns = {}
permanent_warns = {}
afks = {}

@bot.event
async def on_ready():
    global server_count
    server_count = len(bot.guilds)
    print(f"Bot conectado como {bot.user}. Servidores: {server_count}")

@bot.command()
async def servers_stats(ctx):
    guild = ctx.guild
    members = guild.members
    total = len(members)
    online = len([m for m in members if m.status == discord.Status.online])
    idle = len([m for m in members if m.status == discord.Status.idle])
    dnd = len([m for m in members if m.status == discord.Status.dnd])
    offline = total - (online + idle + dnd)
    playing = len([m for m in members if m.activity and m.activity.type == discord.ActivityType.playing])
    listening = len([m for m in members if m.activity and m.activity.type == discord.ActivityType.listening])

    embed = discord.Embed(title="📊 Estadísticas del Servidor", color=discord.Color.green())
    embed.add_field(name="Total de miembros", value=str(total), inline=False)
    embed.add_field(name="Online", value=str(online), inline=True)
    embed.add_field(name="Idle", value=str(idle), inline=True)
    embed.add_field(name="DND", value=str(dnd), inline=True)
    embed.add_field(name="Offline", value=str(offline), inline=True)
    embed.add_field(name="Jugando", value=str(playing), inline=True)
    embed.add_field(name="Escuchando", value=str(listening), inline=True)

    await ctx.send(embed=embed, ephemeral=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def warn(ctx, member: discord.Member, *, reason="No especificado"):
    if is_high_rank(member):
        await ctx.send("No puedes warnear a un alto rango.")
        return
    warns.setdefault(member.id, []).append(reason)
    await ctx.send(f"⚠️ {member.mention} ha sido warneado. Motivo: {reason}")

@bot.command()
@commands.is_owner()
async def warnperm(ctx, member: discord.Member, *, reason="No especificado"):
    permanent_warns.setdefault(member.id, []).append(reason)
    await ctx.send(f"⚠️ {member.mention} ha recibido un WARN PERMANENTE. Motivo: {reason}")

@bot.command()
@commands.has_permissions(administrator=True)
async def unwarn(ctx, member: discord.Member):
    if member.id in warns:
        warns[member.id].pop()
        await ctx.send(f"{member.mention} ha sido unwarned.")
    else:
        await ctx.send("Este usuario no tiene warns comunes.")

@bot.command()
@commands.is_owner()
async def unwarnperm(ctx, member: discord.Member):
    if member.id in permanent_warns:
        permanent_warns[member.id].clear()
        await ctx.send(f"{member.mention} ha sido removido de los WARN PERMANENTES.")
    else:
        await ctx.send("Este usuario no tiene warns permanentes.")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, tiempo="0", apelable="False", *, reason="No especificado"):
    if is_high_rank(member):
        await ctx.send("No puedes banear a un alto rango.")
        return
    tiempo_str = f"Tiempo: {tiempo}"
    apelable_str = f"Apelar: {apelable}"
    await member.ban(reason=reason)
    await ctx.send(f"🔨 El jugador ha sido baneado. Motivo: {reason} | {tiempo_str} | {apelable_str}")

@bot.command()
async def tempban(ctx, member: discord.Member, tiempo: int, *, reason="No especificado"):
    if is_high_rank(member):
        await ctx.send("No puedes banear a un alto rango.")
        return
    await member.ban(reason=reason)
    await ctx.send(f"🔨 El jugador ha sido baneado temporalmente por {tiempo} minutos. Motivo: {reason}")
    await asyncio.sleep(tiempo * 60)  # Tiempo en minutos
    await member.unban(reason="Tempban ha finalizado.")
    await ctx.send(f"{member.mention} ha sido desbaneado después del ban temporal.")

@bot.command()
async def mute(ctx, member: discord.Member, tiempo: int):
    if is_high_rank(member):
        await ctx.send("No puedes mutear a un alto rango.")
        return
    mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if mute_role not in member.roles:
        await member.add_roles(mute_role)
        await ctx.send(f"{member.mention} ha sido muteado por {tiempo} minutos.")
        await asyncio.sleep(tiempo * 60)  # Tiempo en minutos
        await member.remove_roles(mute_role)
        await ctx.send(f"{member.mention} ha sido desmuteado.")
    else:
        await ctx.send(f"{member.mention} ya está muteado.")

@bot.command()
async def afk(ctx, *, reason="AFK"):
    afks[ctx.author.id] = reason
    await ctx.send(f"{ctx.author.mention} está ahora AFK: {reason}")

@bot.command()
async def unafk(ctx):
    if ctx.author.id in afks:
        afks.pop(ctx.author.id)
        await ctx.send(f"{ctx.author.mention} ya no está AFK.")
    else:
        await ctx.send("No estás marcado como AFK.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 Se han eliminado {amount} mensajes.", delete_after=5)

@bot.command()
async def roles(ctx):
    embed = discord.Embed(title="🎖 Roles Especiales", color=discord.Color.blue())
    embed.add_field(name="Founder", value="Fundador del servidor.", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No especificado"):
    if is_high_rank(member):
        await ctx.send("No puedes kickear a un alto rango.")
        return
    await member.kick(reason=reason)
    await ctx.send(f"👢 {member.mention} ha sido expulsado. Motivo: {reason}")

@bot.command()
async def userinfo(ctx, member: discord.Member):
    embed = discord.Embed(title=f"Información de {member.name}", color=discord.Color.blue())
    embed.add_field(name="ID", value=str(member.id))
    embed.add_field(name="Fecha de unión", value=str(member.joined_at))
    embed.add_field(name="Fecha de creación", value=str(member.created_at))
    embed.add_field(name="Roles", value=", ".join([role.name for role in member.roles[1:]]))  # Excluir el rol @everyone
    await ctx.send(embed=embed)

@bot.event
async def on_guild_join(guild):
    global server_count
    server_count += 1
    print(f"Nuevo servidor añadido: {guild.name} | Total: {server_count}")


def is_high_rank(member):
    high_roles = ["Founder", "Owner", "Admin"]
    return any(role.name in high_roles for role in member.roles)

bot.run("TU_TOKEN_AQUI")
