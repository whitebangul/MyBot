from discord.ext import commands
import discord
import random

SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

def create_deck():
    return [f"{rank}{suit}" for suit in SUITS for rank in RANKS]

class PokerGame:
    def __init__(self):
        self.players = {} # {user id: [card1, card2]}
        self.community_cards = []
        self.deck = create_deck()
        random.shuffle(self.deck)
        self.started = False

    def add_player(self, user):
        if self.started:
            return False
        if user.id not in self.players:
            self.players[user.id] = []
            return True
        return False
    
    def deal(self):
        for player_id in self.players:
            self.players[player_id] = [self.deck.pop(), self.deck.pop()]

    def flop(self):
        self.community_cards.extend([self.deck.pop() for _ in range(3)])

    def turn(self):
        self.community_cards.append(self.deck.pop())

    def river(self):
        self.community_cards.append(self.deck.pop())

class Poker(commands.Cog):
    def __init__(self, bot):
        print(f"⚠️ Poker Cog Loaded - ID: {id(self)}")
        self.bot = bot
        self.games = {} #channel_id: PokerGame
    
    @commands.command(name="poker_rules")
    async def poker_rules(self, ctx):
        print(f"📢 poker_rules triggered by {ctx.author} in {ctx.channel}")
        rules_text = (
            "**텍사스 홀덤 게임 설명**\n"
            "\n"
            "**게임 목표:**\n"
            "최고의 5장의 카드 조합을 만들어 승리하세요!\n"
            "\n"
            "**게임 진행 순서:**\n"
            "1. `-poker start` 게임 시작\n"
            "2. `-poker join` 플레이어 참가 (여러 명 가능)\n"
            "3. `-poker deal` 각 플레이어에게 카드 2장씩 배분 (DM으로 전송됨)\n"
            "4. `-poker flop` 커뮤니티 카드 3장 공개\n"
            "5. `-poker turn` 커뮤니티 카드 1장 추가 공개\n"
            "6. `-poker river` 마지막 커뮤니티 카드 1장 공개\n"
            "7. `-poker end` 게임을 종료하기를 원하실 경우 언제든 종료할 수 있습니다.\n"
            "\n"
            "게임 방법:\n"
            "\n"
            "1. 모든 플레이어에게 개인 카드 2장이 주어집니다. (deal)\n"
            "2. 플레이어들은 카드 조합을 보고 베팅 여부를 정합니다. 각 플레이어들은 베팅, 레이즈, 콜, 폴드를 할 수 있습니다.\n"
            "3. 모두가 동의했다면 커뮤니티 카드 3장을 공개합니다. (flop)\n"
            "4. 플레이어들은 개인 카드 2장과 커뮤니티 카드를 조합해 높은 족보를 만들어야 합니다.\n"
            "5. 배팅 여부를 정한 뒤, 모두가 동의했다면 4번째 커뮤니티 카드를 공개합니다. (turn)\n"
            "6. 똑같이 배팅 여부를 정한 뒤, 모두가 동의했다면 마지막 커뮤니티 카드를 공개합니다. (river)\n"
            "7. 모든 커뮤니티 카드가 공개됐다면, 플레이어들은 자신의 카드 조합을 공개해 승자를 정합니다.\n"
            "**카드 조합 예시 (강한 순):**\n"
            "로열 플러시 > 스트레이트 플러시 > 포카드 > 풀하우스 > 플러시 > 스트레이트 > 트리플 > 투페어 > 원페어 > 하이카드\n"
            "\n"
            "게임 중 도움이 필요하면 언제든 `-poker_rules`를 입력하세요!"
        )
        try:
            await ctx.author.send(rules_text)
        except discord.Forbidden:
            await ctx.send("❌ DM을 보낼 수 없습니다. DM을 허용해주세요.")
    
    @commands.command(name="poker")
    async def poker_main(self, ctx, action: str):
        channel_id = ctx.channel.id

        if action == 'start':
            if channel_id in self.games:
                await ctx.send("이곳에서는 이미 게임이 진행 중입니다.")
                return
            
            self.games[channel_id] = PokerGame()
            await ctx.send("게임이 시작되었습니다! `-poker join`으로 참가하세요.")

        elif action == 'join':
            game = self.games.get(channel_id)
            if not game:
                return await ctx.send("게임이 아직 시작되지 않았습니다. `-poker start`를 먼저 입력하세요.")
            added = game.add_player(ctx.author)
            if added:
                await ctx.send(f"<@{ctx.author.id}> 님이 게임에 참가했습니다.")
            else:
                await ctx.send("이미 참가중이거나 게임이 시작되었습니다.")

        elif action == "deal":
            game = self.games.get(channel_id)
            if not game:
                return await ctx.send("진행 중인 게임이 없습니다.")
            if game.started:
                return await ctx.send("이미 카드가 배분되었습니다.")
            game.started = True
            game.deal()

            for player_id, cards in game.players.items():
                user = await self.bot.fetch_user(player_id)
                try:
                    await user.send(f"당신의 카드: {cards[0]}, {cards[1]}")
                except:
                    await ctx.send(f"{user.name} 님에게 DM을 보낼 수 없습니다.")
            await ctx.send("카드가 배분되었습니다! `-poker flop`, `turn`, `river` 명령어로 커뮤니티 카드를 공개하세요.")

        elif action == "flop":
            game = self.games.get(channel_id)
            if not game or not game.started:
                return await ctx.send("게임이 아직 시작되지 않았습니다.")
            if len(game.community_cards) >= 3:
                return await ctx.send("이미 플랍이 공개되었습니다.")
            game.flop()
            await ctx.send(f"🃏 플랍: {' | '.join(game.community_cards)}")

        elif action == "turn":
            game = self.games.get(channel_id)
            if not game or len(game.community_cards) < 3:
                return await ctx.send("먼저 플랍을 공개하세요.")
            if len(game.community_cards) >= 4:
                return await ctx.send("턴은 이미 공개되었습니다.")
            game.turn()
            await ctx.send(f"🃏 턴: {' | '.join(game.community_cards)}")

        elif action == "river":
            game = self.games.get(channel_id)
            if not game or len(game.community_cards) < 4:
                return await ctx.send("먼저 턴을 공개하세요.")
            if len(game.community_cards) == 5:
                return await ctx.send("리버는 이미 공개되었습니다.")
            game.river()
            await ctx.send(f"🃏 리버: {' | '.join(game.community_cards)}")

            await ctx.send("🪙 게임이 종료되었습니다. 참여해 주셔서 감사합니다!")
            del self.games[channel_id]  # Clean up
        
        elif action == "end":
            game = self.games.get(channel_id)
            if not game:
                return await ctx.send("진행 중인 게임이 없습니다.")
            
            del self.games[channel_id]
            await ctx.send(f"<@{ctx.author.id}> 님의 요청으로 게임이 종료되었습니다.")


        else:
            await ctx.send("알 수 없는 명령어입니다. 사용 가능한 명령어: `start`, `join`, `deal`, `flop`, `turn`, `river`")

async def setup(bot):
    await bot.add_cog(Poker(bot))