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
            "\n"
            "**카드 조합 예시 (강한 순):**\n"
            "로열 플러시 > 스트레이트 플러시 > 포카드 > 풀하우스 > 플러시 > 스트레이트 > 트리플 > 투페어 > 원페어 > 하이카드\n"
            "\n"
            "게임 중 도움이 필요하면 언제든 `-poker_rules`를 입력하세요!"
        )
        await ctx.send(rules_text)
    
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
                await ctx.send(f"{ctx.author.display_name} 님이 게임에 참가했습니다.")
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
            await ctx.send(f"플랍: {' | '.join(game.community_cards)}")
        elif action == "turn":
            game = self.games.get(channel_id)
            if not game or len(game.community_cards) < 3:
                return await ctx.send("먼저 플랍을 공개하세요.")
            if len(game.community_cards) >= 4:
                return await ctx.send("턴은 이미 공개되었습니다.")
            game.turn()
            await ctx.send(f"턴: {' | '.join(game.community_cards)}")
        elif action == "river":
            game = self.games.get(channel_id)
            if not game or len(game.community_cards) < 4:
                return await ctx.send("먼저 턴을 공개하세요.")
            if len(game.community_cards) == 5:
                return await ctx.send("리버는 이미 공개되었습니다.")
            game.river()
            await ctx.send(f"🃏 리버: {' | '.join(game.community_cards)}")

        else:
            await ctx.send("알 수 없는 명령어입니다. 사용 가능한 명령어: `start`, `join`, `deal`, `flop`, `turn`, `river`")

async def setup(bot):
    await bot.add_cog(Poker(bot))