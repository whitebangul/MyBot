from discord.ext import commands
import discord
import json
import os

ITEM_ALIASES = {
    "d-serum": "D-Serum (+5)",
    "dserum": "D-Serum (+5)",
    "디세럼": "D-Serum (+5)",
    "디-세럼": "D-Serum (+5)",
    "디세람": "D-Serum (+5)",
    "디-세람": "D-Serum (+5)"
}


COIN_FILE = 'data/coins.json'
ITEM_FILE = 'data/inventory.json'
ALIAS_FILE = 'data/aliases.json'

def load_aliases():
    return load_json(ALIAS_FILE)

def is_integer(n):
    try:
        int(n)
        return True
    except ValueError:
        return False

def load_json(path):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump({}, f)
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

class Store(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="잔액")
    async def balance(self, ctx):
        coins = load_json(COIN_FILE)
        user_id = str(ctx.author.id)

        if user_id not in coins:
            coins[user_id] = 0
            save_json(COIN_FILE, coins)

        bal = coins[user_id]
        await ctx.send(f"<@{user_id}> 님의 현재 잔액은 {bal} 코인입니다.")
    
    @commands.command(name="구매")
    async def buy(self, ctx, item_name: str, amt: int = 1):
        coins = load_json(COIN_FILE)
        items = load_json(ITEM_FILE)
        user_id = str(ctx.author.id)

        # Normalize user input: lowercase + remove hyphens/spaces
        normalized_name = item_name.lower().replace("-", "").replace(" ", "")

        # Translate alias to official name
        official_name = ITEM_ALIASES.get(normalized_name, item_name)

        if official_name not in items:
            return await ctx.send("해당 상품이 존재하지 않습니다.")
        if amt < 0:
            return await ctx.send("유효하지 않은 요청입니다.")

        item = items[official_name]
        price, stock = item["price"], item["stock"]
        total = price * amt

        if stock < amt:
            return await ctx.send(f"현재 재고가 부족합니다. 남은 재고: {stock}")
        if coins.get(user_id, 0) < total:
            return await ctx.send(f"코인이 부족합니다. 총 가격: {total} 코인")
        
        coins[user_id] = coins.get(user_id, 0) - total
        item["stock"] -= amt

        save_json(COIN_FILE, coins)
        save_json(ITEM_FILE, items)
        await ctx.send(f"{official_name}을(를) {amt}개 구매했습니다.")


    @commands.command(name="restock")
    async def restock(self, ctx, item_name: str, amt: int):
        items = load_json(ITEM_FILE)
        aliases = load_aliases()

        # Normalize input
        normalized = item_name.lower().replace("-", "").replace(" ", "")
        official_name = ITEM_ALIASES.get(normalized, item_name)

        if official_name not in items:
            return await ctx.send("해당 상품이 존재하지 않습니다.")
        
        items[official_name]["stock"] += amt
        save_json(ITEM_FILE, items)
        await ctx.send(f"{official_name}의 재고가 {amt}개 추가되었습니다.")

    @commands.command(name="코인")
    async def change_coins(self, ctx, arg1=None, arg2=None):
        coins = load_json(COIN_FILE)

        # case 1: "-코인 amt" --> give coins to the command user
        if is_integer(arg1) and arg2 is None:
            amt = int(arg1)
            user_id = str(ctx.author.id)
            coins[user_id] = coins.get(user_id, 0) + amt
            if coins[user_id] < 0:
                coins[user_id] = 0
            save_json(COIN_FILE, coins)
            if amt >= 0:
                return await ctx.send(f"<@{user_id}>님의 잔액에 {amt} 코인이 추가되었습니다.")
            else:
                return await ctx.send(f"<@{user_id}>님의 잔액에서 {(amt * -1)} 코인이 차감되었습니다.")

        # case 2: "-코인 @user amt"
        elif len(ctx.message.mentions) > 0 and is_integer(arg2):
            member = ctx.message.mentions[0]
            amt = int(arg2)
            user_id = str(member.id)
            coins[user_id] = coins.get(user_id, 0) + amt
            if coins[user_id] < 0:
                coins[user_id] = 0
            save_json(COIN_FILE, coins)
            if amt >= 0:
                return await ctx.send(f"{member.mention}님의 잔액에 {amt} 코인이 추가되었습니다.")
            else:
                return await ctx.send(f"{member.mention}님의 잔액에서 {(amt * -1)} 코인이 차감되었습니다.")

        await ctx.send("사용법: `-코인 @대상 10` 또는 `-코인 10`")

    @commands.command(name="암거래")
    async def list_items(self, ctx):
        items = load_json(ITEM_FILE)

        if not items:
            return await ctx.send("현재 암거래는 불가능합니다.")
        
        msg_lines = ["**암거래 상점 목록**"]
        for item, data in items.items():
            price = data["price"]
            stock = data["stock"]
            msg_lines.append(f"* **{item}** - {price} 코인 `(재고: {stock})`")
        await ctx.send("\n".join(msg_lines))

async def setup(bot):
    await bot.add_cog(Store(bot))