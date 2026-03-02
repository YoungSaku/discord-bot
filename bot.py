import discord
from discord.ext import commands
import json
import os
from datetime import datetime

# -----------------------------
# 設定
# -----------------------------
TOKEN = os.getenv("TOKEN")
RANKING_CHANNEL_ID = 1477729380556865750  # ランキング送信先チャンネルID

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------------
# データ管理
# -----------------------------
voice_times = {}
team_points = {}
user_points = {}

TEAMS = {
    "グリフィンドール": 0,
    "スリザリン": 0,
    "ハッフルパフ": 0,
    "レイブンクロー": 0
}

# データ読み込み
if os.path.exists("points.json"):
    with open("points.json", "r") as f:
        data = json.load(f)
        team_points = data.get("teams", TEAMS.copy())
        user_points = data.get("users", {})
else:
    team_points = TEAMS.copy()

def save_points():
    with open("points.json", "w") as f:
        json.dump({
            "teams": team_points,
            "users": user_points
        }, f)

# ユーザーのチーム判定（ロール名で判定）
def get_user_team(member):
    for role in member.roles:
        if role.name in TEAMS:
            return role.name
    return None

# -----------------------------
# VC監視
# -----------------------------
@bot.event
async def on_voice_state_update(member, before, after):

    # ✅ 入室（1人でもカウント開始）
    if after.channel and not before.channel:
        voice_times[member.id] = datetime.now()

    # ✅ 退室
    if before.channel and not after.channel:

        if member.id in voice_times:
            start_time = voice_times.pop(member.id)
            minutes = int((datetime.now() - start_time).total_seconds() / 60)

            if minutes > 0:
                # チーム加算
                team = get_user_team(member)
                if team:
                    team_points[team] += minutes

                # 個人加算
                user_points[str(member.id)] = user_points.get(str(member.id), 0) + minutes

                save_points()

        # VCが空になったらランキング送信
        if len(before.channel.members) == 0:
            channel = bot.get_channel(RANKING_CHANNEL_ID)
            if channel:
                await send_rankings(channel)

# -----------------------------
# 表示フォーマット
# -----------------------------
def format_time(minutes):
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}時間{mins}分"

# -----------------------------
# ランキング生成
# -----------------------------
async def send_rankings(channel):

    sorted_teams = sorted(team_points.items(), key=lambda x: x[1], reverse=True)
    sorted_users = sorted(user_points.items(), key=lambda x: x[1], reverse=True)

    rank_words = ["1位", "2位", "3位","4位"]

    # 🔹 寮ランキング（pt表示）
    text = "📊 **寮ランキング**\n\n"
    for i, (team, pts) in enumerate(sorted_teams):
        medal = rank_words[i] if i < len(rank_words) else f"{i+1}位"
        text += f"{medal} {team} – {pts}pt\n"

    # 🔹 個人ランキング（時間＋分表示）
    text += "\n👤 **個人ランキング TOP5**\n\n"
    for i, (user_id, pts) in enumerate(sorted_users[:5]):
        try:
            user = await bot.fetch_user(int(user_id))
            medal = rank_words[i] if i < len(rank_words) else f"{i+1}位"
            text += f"{medal} {user.name} – {format_time(pts)}\n"
        except:
            continue

    await channel.send(text)

# -----------------------------
# コマンド
# -----------------------------
@bot.command(name="ranking")
async def ranking(ctx):
    await send_rankings(ctx.channel)

@bot.command(name="myrank")
async def myrank(ctx):

    user_id = str(ctx.author.id)
    sorted_users = sorted(user_points.items(), key=lambda x: x[1], reverse=True)

    rank = None
    for i, (uid, pts) in enumerate(sorted_users):
        if uid == user_id:
            rank = i + 1
            break

    if rank:
        points = user_points[user_id]
        await ctx.send(f"あなたの順位は **{rank}位**（{format_time(points)}）です！")
    else:
        await ctx.send("まだポイントがありません。")

# -----------------------------
# 起動
# -----------------------------
bot.run(TOKEN)
