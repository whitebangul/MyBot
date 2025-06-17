from discord.ext import commands
import discord
import json
import os

COIN_FILE = 'data/coins.json'
ITEM_FILE = 'data/inventory.json'

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
        bal = coins.get(str(ctx.author.id), 0)
        await ctx.send(f"<@{ctx.author.id}> 님의 현재 잔액은 {bal} 코인입니다.")
    
    @commands.command(name="구매")
    async def buy(self, ctx, item_name: str):
        coins = load_json(COIN_FILE)
        items = load_json(ITEM_FILE)
        user_id = str(ctx.user.id)

        if item_name not in items:
            return await ctx.send("해당 상품이 존재하지 않습니다.")
        item = items[item_name]
        price, stock = item["price"], item["stock"]

        if stock <= 0:
            return await ctx.send("현재 재고가 남아있지 않습니다.")
        if coins.get(user_id, 0) < price:
            return await ctx.send("코인이 부족합니다.")
        
        coins[user_id] = coins.get(user_id, 0) - price
        item["stock"] -= 1

        save_json(COIN_FILE, coins)
        save_json(ITEM_FILE, items)
        await ctx.send(f"{item_name}을(를) 구매했습니다.")

    @commands.command(name="restock")
    async def restock(self, ctx, item_name: str, amt: int):
        items = load_json(ITEM_FILE)
        if item_name not in items:
            return await ctx.send("해당 상품이 존재하지 않습니다.")
        items[item_name]["stock"] += amt
        save_json(ITEM_FILE, items)
        await ctx.send(f"{item_name}의 재고가 {amt}개 추가되었습니다.")

    @commands.command(name="add")
    async def add_coins(self, ctx, member: discord.Member, amt: int):
        coins = load_json(COIN_FILE)
        user_id = str(member.id)

        coins[user_id] = coins.get(user_id, 0) + amt
        save_json(COIN_FILE, coins)

        await ctx.send(f"{member.mention}님의 잔액에 {amt} 코인이 추가되었습니다.")

    @commands.command(name="암거래")
    async def list_items(self, ctx):
        items = load_json(ITEM_FILE)

        if not items:
            return await ctx.send("현재 암거래는 불가능합니다.")
        
        msg_lines = ["**암거래 상점 목록**"]
        for item, data in items.items():
            price = data["price"]
            stock = data["stock"]
            msg_lines.append(f"* **{item}** - {price} 코인 (재고: {stock})")
        await ctx.send("\n".join(msg_lines))

async def setup(bot):
    await bot.add_cog(Store(bot))