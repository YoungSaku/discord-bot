import discord
from discord.ext import commands
import json
import os
from datetime import datetime

TOKEN = os.getenv("TOKEN")
RANKING_CHANNEL_ID = 1477729380556865750  # rankチャンネルID

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

voice_times = {}
team_points = {}
user_points = {}

TEAMS = {
    "ぐりふぃんどーる": 0,
    "すりざりん": 0,
    "はっふるぱふ": 0,
    "れいぶんくろー": 0
}

# -----------------------------
# データ読み込み
# -----------------------------
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

def get_user_team(member):
    for role in member.roles:
        if role.name in TEAMS:
            return role.name
    return None

# -----------------------------
# 起動時同期（スラッシュ）
# -----------------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")
    print("スラッシュコマンド同期完了")

# -----------------------------
# VC監視
# -----------------------------
@bot.event
async def on_voice_state_update(member, before, after):

    # 入室
    if after.channel and not before.channel:
        if len(after.channel.members) >= 2:
            voice_times[member.id] = datetime.now()

    # 退室
    if before.channel and not after.channel:

        if member.id in voice_times:
            start_time = voice_times.pop(member.id)
            minutes = int((datetime.now() - start_time).total_seconds() / 60)

            # 抜けた後も1人以上いた（2人以上で成立）
            if len(before.channel.members) >= 1:
                team = get_user_team(member)
                if team:
                    team_points[team] += minutes

                user_points[str(member.id)] = user_points.get(str(member.id), 0) + minutes
                save_points()

        # VCが完全終了したらランキング送信
        if len(before.channel.members) == 0:
            channel = bot.get_channel(RANKING_CHANNEL_ID)
            if channel:
                await send_rankings(channel)

# -----------------------------
# ランキング生成
# -----------------------------
async def send_rankings(channel):

    sorted_teams = sorted(team_points.items(), key=lambda x: x[1], reverse=True)
    sorted_users = sorted(user_points.items(), key=lambda x: x[1], reverse=True)

    medals = ["🥇", "🥈", "🥉"]

    text = "📊 **寮ランキング**\n\n"

    for i, (team, pts) in enumerate(sorted_teams):
        medal = medals[i] if i < 3 else f"{i+1}位"
        text += f"{medal} {team} – {pts}pt\n"

    text += "\n👤 **個人ランキング TOP5**\n\n"

    for i, (user_id, pts) in enumerate(sorted_users[:5]):
        try:
            user = await bot.fetch_user(int(user_id))
            medal = medals[i] if i < 3 else f"{i+1}位"
            text += f"{medal} {user.name} – {pts}分\n"
        except:
            continue

    await channel.send(text)

# -----------------------------
# スラッシュコマンド
# -----------------------------
@bot.tree.command(name="ranking", description="現在のランキングを見る")
async def ranking(interaction: discord.Interaction):
    await interaction.response.defer()
    await send_rankings(interaction.channel)

@bot.tree.command(name="myrank", description="自分の順位を見る")
async def myrank(interaction: discord.Interaction):

    user_id = str(interaction.user.id)
    sorted_users = sorted(user_points.items(), key=lambda x: x[1], reverse=True)

    rank = None
    for i, (uid, pts) in enumerate(sorted_users):
        if uid == user_id:
            rank = i + 1
            break

    if rank:
        points = user_points[user_id]
        await interaction.response.send_message(
            f"あなたの順位は **{rank}位**（{points}分）です！"
        )
    else:
        await interaction.response.send_message("まだポイントがありません。")

# -----------------------------
# 起動
# -----------------------------
bot.run(TOKEN)

