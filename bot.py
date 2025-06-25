import discord
from discord.ext import commands
from discord.utils import get
from datetime import datetime
import asyncio
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# Datos de estado
server_count = 0
banned_users = {}
warns = {}
permanent_warns = {}
afks = {}

# Roles que no pueden ser moderados
HIGH_ROLES = {"Founder", "Owner", "Admin"}

# ----------------------- Eventos -----------------------

@bot.event
async def on_ready():
    global server_count
    server_count = len(bot.guilds)
    print(f"✅ Bot conectado como {bot.user} | Servidores: {server_count}")

@bot.event
async def on_guild_join(guild):
    global server_count
    server_count += 1
    print(f"➕ Nuevo servidor: {guild.name} | Total: {server_count}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 No tienes permisos para ejecutar este comando.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Faltan argumentos requeridos.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Comando no encontrado.")
    else:
        await ctx.send(f"⚠️ Error: {str(error)}")

# ----------------------- Utilidades -----------------------

def is_high_rank(member):
    return any(role.name in HIGH_ROLES for role in member.roles)

# ----------------------- Comandos -----------------------

@bot.command()
async def servers_stats(ctx):
    guild = ctx.guild
    members = guild.members
    total = len(members)
    statuses = {
        "Online": discord.Status.online,
        "Idle": discord.Status.idle,
        "DND": discord.Status.dnd
    }
    counts = {k: len([m for m in members if m.status == v]) for k, v in statuses.items()}
    offline = total - sum(counts.values())
    playing = len([m for m in members if m.activity and m.activity.type == discord.ActivityType.playing])
    listening = len([m for m in members if m.activity and m.activity.type == discord.ActivityType.listening])

    embed = discord.Embed(title="📊 Estadísticas del Servidor", color=discord.Color.green())
    embed.add_field(name="Total de miembros", value=total, inline=False)
    for status, count in counts.items():
        embed.add_field(name=status, value=count, inline=True)
    embed.add_field(name="Offline", value=offline, inline=True)
    embed.add_field(name="Jugando", value=playing, inline=True)
    embed.add_field(name="Escuchando", value=listening, inline=True)

    await ctx.send(embed=embed, ephemeral=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def warn(ctx, member: discord.Member, *, reason="No especificado"):
    if is_high_rank(member):
        return await ctx.send("🚫 No puedes warnear a un alto rango.")
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
    if warns.get(member.id):
        warns[member.id].pop()
        await ctx.send(f"✅ {member.mention} ha sido unwarned.")
    else:
        await ctx.send("❌ Este usuario no tiene warns comunes.")

@bot.command()
@commands.is_owner()
async def unwarnperm(ctx, member: discord.Member):
    if permanent_warns.get(member.id):
        permanent_warns[member.id].clear()
        await ctx.send(f"✅ {member.mention} ha sido limpiado de WARN PERMANENTES.")
    else:
        await ctx.send("❌ Este usuario no tiene warns permanentes.")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, tiempo="0", apelable="False", *, reason="No especificado"):
    if is_high_rank(member):
        return await ctx.send("🚫 No puedes banear a un alto rango.")
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member.mention} ha sido baneado. Motivo: {reason} | Tiempo: {tiempo} | Apelable: {apelable}")

@bot.command()
async def tempban(ctx, member: discord.Member, tiempo: int, *, reason="No especificado"):
    if is_high_rank(member):
        return await ctx.send("🚫 No puedes banear a un alto rango.")
    await member.ban(reason=reason)
    await ctx.send(f"⏳ {member.mention} baneado por {tiempo} minutos. Motivo: {reason}")
    await asyncio.sleep(tiempo * 60)
    await ctx.guild.unban(member)
    await ctx.send(f"✅ {member.name} ha sido desbaneado después del tempban.")

@bot.command()
async def mute(ctx, member: discord.Member, tiempo: int):
    if is_high_rank(member):
        return await ctx.send("🚫 No puedes mutear a un alto rango.")
    mute_role = get(ctx.guild.roles, name="Muted")
    if not mute_role:
        return await ctx.send("❌ Rol 'Muted' no encontrado.")
    if mute_role in member.roles:
        return await ctx.send(f"{member.mention} ya está muteado.")
    await member.add_roles(mute_role)
    await ctx.send(f"🔇 {member.mention} muteado por {tiempo} minutos.")
    await asyncio.sleep(tiempo * 60)
    await member.remove_roles(mute_role)
    await ctx.send(f"🔊 {member.mention} ha sido desmuteado.")

@bot.command()
async def afk(ctx, *, reason="AFK"):
    afks[ctx.author.id] = reason
    await ctx.send(f"🌙 {ctx.author.mention} está ahora AFK: {reason}")

@bot.command()
async def unafk(ctx):
    if afks.pop(ctx.author.id, None):
        await ctx.send(f"✅ {ctx.author.mention} ya no está AFK.")
    else:
        await ctx.send("❌ No estás marcado como AFK.")

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
        return await ctx.send("🚫 No puedes kickear a un alto rango.")
    await member.kick(reason=reason)
    await ctx.send(f"👢 {member.mention} ha sido expulsado. Motivo: {reason}")

@bot.command()
async def userinfo(ctx, member: discord.Member):
    embed = discord.Embed(title=f"📋 Info de {member}", color=discord.Color.blue())
    embed.add_field(name="🆔 ID", value=member.id)
    embed.add_field(name="🕒 Unión", value=member.joined_at.strftime('%d/%m/%Y %H:%M'))
    embed.add_field(name="📆 Creación", value=member.created_at.strftime('%d/%m/%Y %H:%M'))
    roles = [role.name for role in member.roles[1:]]
    embed.add_field(name="🎭 Roles", value=", ".join(roles) if roles else "Ninguno")
    await ctx.send(embed=embed)

# ----------------------- Ejecución -----------------------

bot.run("TOKEN_HERE")
