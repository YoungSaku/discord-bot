import discord
from discord.ext import commands
import json
import os
from datetime import datetime

# -----------------------------
# 設定
# -----------------------------
TOKEN = os.getenv("TOKEN")
GUILD_ID = 1237998527981031456  # 対象サーバーIDに置き換え
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
# 起動時同期（ギルド単位）
# -----------------------------
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)
    print(f"Logged in as {bot.user}")
    print("スラッシュコマンドをギルド単位で同期完了")

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

        # VCが完全終了したらランキング送信（固定チャンネル）
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

    rank_words = ["1位", "2位", "3位","4位"]

    text = "📊 **寮ランキング**\n\n"
    for i, (team, pts) in enumerate(sorted_teams):
        medal = rank_words[i] if i < 3 else f"{i+1}位"
        text += f"{medal} {team} – {pts}pt\n"

    text += "\n👤 **個人ランキング TOP5**\n\n"
    for i, (user_id, pts) in enumerate(sorted_users[:5]):
        try:
            user = await bot.fetch_user(int(user_id))
            medal = rank_words[i] if i < 3 else f"{i+1}位"
            text += f"{medal} {user.name} – {pts}分\n"
        except:
            continue

    await channel.send(text)

# -----------------------------
# スラッシュコマンド（ギルド単位）
# -----------------------------
@bot.tree.command(
    name="ranking",
    description="現在のランキングを見る",
    guild=discord.Object(id=GUILD_ID)
)
async def ranking(interaction: discord.Interaction):
    await interaction.response.defer()
    channel = bot.get_channel(RANKING_CHANNEL_ID)
    if channel:
        await send_rankings(channel)

@bot.tree.command(
    name="myrank",
    description="自分の順位を見る",
    guild=discord.Object(id=GUILD_ID)
)
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
