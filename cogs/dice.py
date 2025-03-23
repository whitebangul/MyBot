from discord.ext import commands
import random
import re

class Dice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        print(f"[DEBUG] Received message: {message.content}")
        if message.author == self.bot.user:
            return
        
        content = message.content.lower().replace(" ", "")
        match = re.match(r"^(\d+)d(\d+)(?:\s*([+\-*/])\s*(\d+))?(?:\s+(.*))?", content)
        if match:
        
            print("received message")
            rolls, sides, operator, number = match.groups()
            rolls, sides = int(rolls), int(sides)
            print(f"Operator: {operator}, Number: {number}")
            if rolls <=0 or sides <= 0:
                return
            
            results = [random.randint(1, sides) for _ in range(rolls)]
            total = sum(results)
            raw_total = total

            if operator and number:
                number = int(number)
                if operator == '+':
                    total += number
                elif operator == '-':
                    total -= number
                elif operator == '*':
                    total *= number
                elif operator == '/':
                    total = round(total, number) if number != 0 else 0

            rolled_str = ", ".join(str(r) for r in results)
            op_str = f" {operator} {number}" if operator and number else ""

            await message.reply(
                f"🎲 주사위: {rolls}d{sides}{op_str} 결과: {total} `(굴림: {rolled_str})`"
            )
            return
        await self.bot.process_commands(message)

async def setup(bot):
    await bot.add_cog(Dice(bot))
