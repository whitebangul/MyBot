from discord.ext import commands
import discord
from .blackjackgame import BlackJackGame

class BlackjackView(discord.ui.View):
    def __init__(self, game, pid):
        super().__init__()
        self.game = game
        self.pid = pid
        self.message = None
    
    async def on_timeout(self):
        if self.game.is_game_over():
            return
        self.disable_all_items()
        if self.message:
            try:
                await self.message.edit(content="시간이 초과되어 게임이 종료되었습니다.", view=None)
            except discord.NotFound:
                pass

    async def interaction_check(self, interaction: discord.Interaction[discord.Client]) -> bool:
        if interaction.user.id != self.pid:
            await interaction.response.send_message("이 게임은 당신의 것이 아닙니다!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="히트", style=discord.ButtonStyle.primary)
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = self.game.hit()
        msg = self.game.get_hands()
        if result:
            msg += f"\n {result}"
            self.disable_all_items()
            self.stop()
        await interaction.response.edit_message(content=msg, view=self if not self.game.is_game_over() else None)
    
    @discord.ui.button(label="스탠드", style=discord.ButtonStyle.red)
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = self.game.stand()
        msg = self.game.get_hands(reveal_dealer = True)
        msg += f"\n {result}"
        self.disable_all_items()
        self.stop()
        await interaction.response.edit_message(content=msg, view=None)
    
    def disable_all_items(self):
        for child in self.children:
            child.disabled = True

bj_rules = (
    "**블랙잭 게임 규칙**\n\n"
    "1. 딜러(도박꾼)과 1:1로 진행됩니다.\n"
    "2. 목표는 21을 넘지 않으면서 가장 높은 숫자를 만드는 것입니다.\n"
    "3. J, Q, K는 10점, A는 1 또는 11점으로 계산됩니다.\n"
    "4. 베팅은 게임 시작 직후 1~5 코인까지 가능합니다.\n"
    "5. 승리 시 배팅 금액의 2배를 획득합니다.\n"
    "6. 비기면 코인을 돌려받고, 지면 코인을 잃습니다.\n"
    "\n"
    "명령어:\n"
    "`-블랙잭 시작` 게임 시작\n"
    "`-블랙잭 베팅 <금액>` 베팅 (1~5 코인)\n"
    "`-블랙잭 규칙` 규칙 보기\n"
)

class BlackJack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}  # user_id: BlackJackGame
    
    @commands.command(name="블랙잭")
    async def blackjack(self, ctx, act: str = None, amt: int = None):
        pid = ctx.author.id

        if act == "규칙":
            await ctx.send(bj_rules)
        
        elif act == "시작":
            self.games[pid] = BlackJackGame(pid)
            await ctx.send("🃏 블랙잭 게임을 시작했습니다. `-블랙잭 베팅 <금액>` 으로 베팅해주세요.")
            await ctx.send(self.games[pid].get_hands())
        
        elif act == "베팅":
            game = self.games.get(pid)
            if not game:
                return await ctx.send("게임을 먼저 시작해주세요. `-blackjack start`")
            
            if amt is None:
                return await ctx.send("베팅 금액을 입력해주세요. 예: `-blackjack bet 3`")

            success, msg = game.place_bet(amt)
            await ctx.send(msg)
            if success:
                # 🎯 Check if the player got 21 right after betting
                if game.check_initial_blackjack():
                    game.game_over = True
                    result = game.end_game()
                    await ctx.send(game.get_hands(reveal_dealer=True))
                    await ctx.send(f"**블랙잭!** {result}")
                else:
                    view = BlackjackView(game, pid)
                    view.message = await ctx.send(game.get_hands(), view=view)
        
        elif act == "힛":
            game = self.games.get(pid)
            if not game:
                return await ctx.send("게임을 먼저 시작해주세요. `-blackjack start`")
            
            result = game.hit()
            await ctx.send(game.get_hands())
            if result:
                await ctx.send(f"{result}")
        
        elif act == "스탠드":
            game = self.games.get(pid)
            if not game:
                return await ctx.send("게임을 먼저 시작해주세요. `-blackjack start`")
            
            result = game.stand()
            await ctx.send(game.get_hands(reveal_dealer=True))
            await ctx.send(f"{result}")
        
        elif act == "status":
            game = self.games.get(pid)
            if not game:
                return await ctx.send("진행 중인 게임이 없습니다.")
            await ctx.send(game.get_hands())
        
        else:
            await ctx.send("알 수 없는 명령어입니다. `블랙잭 규칙`을 통해 사용 가능한 명령어를 확인하세요.")

async def setup(bot):
    await bot.add_cog(BlackJack(bot))
