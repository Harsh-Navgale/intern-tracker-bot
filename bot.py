import discord
from discord.ext import commands
from db import init_db, log_message, get_logs_by_date, get_user_logs
from datetime import datetime, date
import os
from main import keep_alive

keep_alive()

config = {
    "TOKEN": os.getenv("TOKEN"),
    "TRACK_CHANNEL_ID": int(os.getenv("TRACK_CHANNEL_ID"))
}

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

init_db()

# Check if user has 'interns' role
def has_interns_role(member):
    for role in member.roles:
        if role.name.lower() == "interns":
            return True
    return False

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.channel.id == config["TRACK_CHANNEL_ID"] and not message.author.bot:
        content = message.content.lower()
        start_keywords = ["start", "starting", "begin", "work start", "started"]
        end_keywords = ["end", "ended", "end work", "day end", "work done", "done for today", "finished", "analyzed", "analysed", "complete", "done", "create", "work", "going", "through", "wrote", "made"]

        if any(kw in content for kw in start_keywords):
            if has_interns_role(message.author):
                log_message(str(message.author.id), str(message.author), "start")
                await message.channel.send(f"{message.author.mention} Start logged ✅")
            else:
                await message.channel.send(f"{message.author.mention} You don't have the 'interns' role. You cannot log start time.")
        
        elif any(kw in content for kw in end_keywords):
            if has_interns_role(message.author):
                log_message(str(message.author.id), str(message.author), "end")
                await message.channel.send(f"{message.author.mention} End logged ✅")
            else:
                await message.channel.send(f"{message.author.mention} You don't have the 'interns' role. You cannot log end time.")
    await bot.process_commands(message)

@bot.command()
async def status(ctx):
    logs = get_logs_by_date(date.today().isoformat())
    starters = {user_id for user_id, t in logs if t == 'start'}
    enders = {user_id for user_id, t in logs if t == 'end'}

    interns_role = discord.utils.get(ctx.guild.roles, name="interns")
    if not interns_role:
        await ctx.send("❌ 'interns' role not found in this server.")
        return

    missing_start = []
    missing_end = []

    for member in interns_role.members:
        if not member.bot:
            if str(member.id) not in starters:
                missing_start.append(member.mention)
            if str(member.id) not in enders:
                missing_end.append(member.mention)

    await ctx.send(f"🔍 **Start not logged:**\n{', '.join(missing_start) or '✅ All done!'}")
    await ctx.send(f"🔍 **End not logged:**\n{', '.join(missing_end) or '✅ All done!'}")


@bot.command()
async def log(ctx, member: discord.Member):
    logs = get_user_logs(str(member.id))
    if not logs:
        await ctx.send(f"No logs for {member.display_name}")
    else:
        log_text = "\n".join([f"{l[3]} - {l[2].capitalize()} at {l[4]}" for l in logs])
        await ctx.send(f"📜 Logs for {member.display_name}:\n{log_text}")

bot.run(config["TOKEN"])
