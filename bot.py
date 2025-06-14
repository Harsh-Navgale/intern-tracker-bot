import discord
from discord.ext import commands
from db import init_db, log_message, get_logs_by_date, get_user_logs, get_all_logs
from datetime import datetime, date, time
import os
from main import keep_alive
from discord.ext.commands import has_permissions, CheckFailure
import csv
from fpdf import FPDF
import io
import asyncio
import pytz
from collections import defaultdict
from discord.ext import tasks


inactive_counts = defaultdict(int)
warned_users = set()

keep_alive()

config = {
    "TOKEN": os.getenv("TOKEN"),
    "TRACK_CHANNEL_ID": "1334516016759443463"
}

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
intents.presences = True  # REQUIRED to get user status!

bot = commands.Bot(command_prefix='!', intents=intents)

init_db()

# Check if user has 'interns' role
def has_interns_role(member):
    print(f"Roles for {member.name}: {[role.name for role in member.roles]}")
    return any(role.name.lower() == "interns" for role in member.roles)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.channel.id == config["TRACK_CHANNEL_ID"] and not message.author.bot:
        content = message.content.lower()
        start_keywords = ["starting"]
        end_keywords = ["end", "ended", "end work", "day end", "work done", "done for today", "finished", "analyzed", "learn", "attend", "attended", "learned", "analysed", "complete","working on","found","vulnerablities","vulnerabl", "done", "create", "work", "going", "through", "wrote", "made"]

        if any(kw in content for kw in start_keywords):
            if has_interns_role(message.author):
                log_message(str(message.author.id), str(message.author.display_name), "start", content, datetime.now().isoformat())
                await message.channel.send(f"{message.author.mention} Start logged ✅")
            else:
                await message.channel.send(f"{message.author.mention} You don't have the 'interns' role. You cannot log start time.")
        
        elif any(kw in content for kw in end_keywords):
            if has_interns_role(message.author):
                log_message(str(message.author.id), str(message.author.display_name), "end", content, datetime.now().isoformat())
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

def is_admin():
    async def predicate(ctx):
        admin_role = discord.utils.get(ctx.guild.roles, name="Admin")
        return admin_role in ctx.author.roles
    return commands.check(predicate)

@bot.command()
@is_admin()
async def log(ctx, member: discord.Member):
    logs = get_user_logs(str(member.id))
    if not logs:
        await ctx.send(f"No logs for {member.display_name}")
    else:
        log_text = "\n".join([f"[{l[5]}] ({l[3].capitalize()}): {l[4]}" for l in logs])
        await ctx.send(f"📜 Logs for {member.display_name}:\n{log_text}")

@bot.command()
@is_admin()
async def export_csv(ctx):
    logs = get_all_logs()
    if not logs:
        await ctx.send("No logs found.")
        return

    filename = "logs_export.csv"
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "User ID", "Username", "Type", "Message", "Timestamp", "Date"])
        for row in logs:
            writer.writerow(row)

    await ctx.send(file=discord.File(filename))

@bot.command()
@is_admin()
async def export_pdf(ctx):
    logs = get_all_logs()
    if not logs:
        await ctx.send("No logs found.")
        return

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Intern Logs Export", ln=True, align="C")

    for row in logs:
        log_line = f"[{row[5]}] ({row[3].capitalize()}) {row[2]}: {row[4]}"
        pdf.cell(200, 10, txt=log_line, ln=True)

    filename = "logs_export.pdf"
    pdf.output(filename)
    await ctx.send(file=discord.File(filename))

ADMIN_USER_ID = 735882589075669012  # Replace with your actual Discord user ID

#@tasks.loop(minutes=30)
#async def check_intern_activity():
    #now = datetime.now(IST).time()
    #if dtime(14, 0) <= now <= dtime(21, 0):  # Between 2 PM and 9 PM IST
        #for guild in bot.guilds:
            #interns_role = discord.utils.get(guild.roles, name="interns")
            #if not interns_role:
                #print(f"'Interns' role not found in {guild.name}")
                #continue

            #for member in interns_role.members:
                #if member.status in [discord.Status.offline, discord.Status.idle, discord.Status.invisible]:
                    #inactive_counts[member.id] += 1

                    # DM only if they've been inactive more than once
                    #if inactive_counts[member.id] > 1 and member.id not in warned_users:
                        #try:
                            #warning_msg = (
                                #f"⚠️ {member.display_name} is inactive during working hours (2 PM – 9 PM IST)."
                            #)
                            #await member.send("⚠️ You're inactive during working hours (2 PM – 9 PM IST). Please come online.")
                            
                            # DM admin too
                            #admin_user = await bot.fetch_user(ADMIN_USER_ID)
                            #await admin_user.send(warning_msg)

                            #warned_users.add(member.id)
                        #except Exception as e:
                            #print(f"Could not DM {member.display_name}: {e}")
               # else:
                    # Reset their inactivity if they are online again
                    #inactive_counts[member.id] = 0
                    #warned_users.discard(member.id)



bot.run(config["TOKEN"])
