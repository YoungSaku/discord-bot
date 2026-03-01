import discord
from discord.ext import commands
import time
import json
import os

# ====== Intents ======
intents = discord.Intents.default()
intents.voice_states = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ====== データ ======
voice_start = {}
team_points = {
    "グリフィンドール": 0,
    "スリザリン": 0,
    "レイブンクロー": 0,
    "ハッフルパフ": 0
}

DATA_FILE = "points.json"

# ====== 保存・読み込み ======
def save_points():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(team_points, f, ensure_ascii=False)

def load_points():
    global team_points
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            team_points = json.load(f)

# ====== 寮判定 ======
def get_team(member):
    roles = [r.name for r in member.roles]

    if "グリフィンドール" in roles:
        return "グリフィンドール"
    elif "スリザリン" in roles:
        return "スリザリン"
    elif "レイブンクロー" in roles:
        return "レイブンクロー"
    elif "ハッフルパフ" in roles:
        return "ハッフルパフ"

    return None

# ====== 起動時 ======
@bot.event
async def on_ready():
    load_points()
    print(f"Logged in as {bot.user}")

# ====== 通話監視 ======
@bot.event
async def on_voice_state_update(member, before, after):

    # 通話入室
    if before.channel is None and after.channel is not None:
        voice_start[member.id] = time.time()

    # 通話退出
    elif before.channel is not None and after.channel is None:
        start_time = voice_start.get(member.id)

        if start_time:
            duration = time.time() - start_time
            minutes = int(duration // 60)  # 1分=1ポイント

            team = get_team(member)

            if team and minutes > 0:
                team_points[team] += minutes
                save_points()

            del voice_start[member.id]

# ====== ポイント表示 ======
@bot.command()
async def points(ctx):
    msg = "🏰 寮ポイント 🏰\n"
    for team, point in team_points.items():
        msg += f"{team}：{point} pt\n"

    await ctx.send(msg)

# ====== ランキング ======
@bot.command()
async def housecup(ctx):
    sorted_teams = sorted(team_points.items(), key=lambda x: x[1], reverse=True)

    msg = "🏆 ホグワーツ杯ランキング 🏆\n"
    for i, (team, point) in enumerate(sorted_teams, 1):
        msg += f"{i}. {team} - {point} pt\n"

    await ctx.send(msg)

# ====== 起動 ======
bot.run(os.getenv("TOKEN"))
