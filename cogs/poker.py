from discord.ext import commands
import discord
import random
from .bettings import Betting

from phevaluator.evaluator import evaluate_cards

SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

rules_text = (
            "**텍사스 홀덤 게임 설명**\n"
            "\n"
            "**게임 목표:**\n"
            "최고의 5장의 카드 조합을 만들어 승리하세요!\n"
            "\n"
            "**게임 명령어:**\n"
            "1. `-텍사스 시작` 게임 시작\n"
            "2. `-텍사스 참가` 플레이어 참가 (여러 명 가능)\n"
            "3. `-텍사스 배분` 각 플레이어에게 카드 2장씩 배분 (DM으로 전송)\n"
            "4. `-텍사스 플랍` 공유 카드 3장 공개\n"
            "5. `-텍사스 턴` 공유 카드 1장 추가 공개\n"
            "6. `-텍사스 리버` 마지막 공유 카드 1장 공개\n"
            "7. `-텍사스 종료` 게임을 종료하기를 원하실 경우 언제든 종료할 수 있습니다.\n"
            "8. `-텍사스 규칙` 텍사스 홀덤의 규칙을 확인합니다.\n"
            "\n"
            "**베팅 명령어:**\n"
            "1. `-텍사스 베팅 <금액>` 베팅 라운드 시작 시 첫 플레이어의 베팅\n"
            "2. `-텍사스 콜` 현재 베팅 액수에 응할\n"
            "4. `-텍사스 폴드` 해당 라운드 포기\n"
            "\n"
            "게임 방법:\n"
            "\n"
            "1. 모든 플레이어에게 개인 카드 2장이 주어집니다. (배분)\n"
            "2. 플레이어들은 카드 조합을 보고 베팅 여부를 정합니다. 각 플레이어들은 베팅, 레이즈, 콜, 폴드를 할 수 있습니다.\n"
            "3. 모두가 동의했다면 공유 카드 3장을 공개합니다. (플랍)\n"
            "4. 플레이어들은 개인 카드 2장과 공유 카드로 높은 카드 조합을 만들어야 합니다.\n"
            "5. 배팅 여부를 정한 뒤, 모두가 동의했다면 4번째 공유 카드를 공개합니다. (턴)\n"
            "6. 똑같이 배팅 여부를 정한 뒤, 모두가 동의했다면 마지막 공유 카드를 공개합니다. (리버)\n"
            "7. 모든 공유 카드가 공개됐다면, 플레이어들은 자신의 카드 조합을 공개해 승자를 정합니다.\n"
            "\n"
            "**카드 조합 예시 (강한 순):**\n"
            "로열 플러시 > 스트레이트 플러시 > 포카드 > 풀하우스 > 플러시 > 스트레이트 > 트리플 > 투페어 > 원페어 > 하이카드\n"
            "\n"
            "**베팅 방법**\n"
            "1. 첫 번째 플레이어가 원하는 양의 코인을 베팅합니다.\n"
            "2. 다른 플레이어들은 같은 양의 코인을 베팅하며 `콜`을 하거나, `폴드`를 해 해당 게임을 포기할 수 있습니다.\n"
            "3. 단, `폴드`를 선언할 시 이미 이전에 베팅한 코인은 돌려받을 수 없습니다.\n"
            "4. 첫 번째 플레이어를 제외한 모든 플레이어들은 `콜` 대신 `레이즈`를 선언해 판돈을 올릴 수 있습니다.\n"
            "5. 만일 누군가가 `레이즈`를 선언했다면, 이미 `콜`을 외친 플레이어들도 새로운 판돈에 `콜`로 응할지, `폴드`로 포기할지 선언합니다.\n"
            "6. 이 상태에서 `폴드`를 선언할 경우에도 이미 `콜`을 외치며 베팅한 코인은 돌려받을 수 없습니다.\n"
            "\n"
            "게임 중 도움이 필요하면 언제든 `-포커 규칙`을 입력하세요!"
        )

suit_map = {'♠': 's', '♥': 'h', '♦': 'd', '♣': 'c'}
rank_map = {'10': 'T'}

def convert_card(card):
    for k, v in rank_map.items():
        card = card.replace(k, v)
    rank = card[:-1] if len(card) == 3 else card[0]
    suit = suit_map[card[-1]]
    return rank + suit

def create_deck():
    return [f"{rank}{suit}" for suit in SUITS for rank in RANKS]

class PokerGame:
    def __init__(self):
        self.players = {} # {user id: [card1, card2]}
        self.community_cards = []
        self.deck = create_deck()
        random.shuffle(self.deck)
        self.started = False
        self.betting = Betting()

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
        self.betting.setup_players(self.players)

    def flop(self):
        self.community_cards.extend([self.deck.pop() for _ in range(3)])

    def turn(self):
        self.community_cards.append(self.deck.pop())

    def river(self):
        self.community_cards.append(self.deck.pop())
    
    def evaluate_winner(self):
        if len(self.community_cards) < 5:
            return []
        best_score = None
        winners = []
        for pid, hole_cards in self.players.items():
            all_cards = hole_cards + self.community_cards
            converted = [convert_card(c) for c in all_cards]
            score = evaluate_cards(*converted)
            if best_score is None or score < best_score:
                best_score = score
                winners = [pid]
            elif score == best_score:
                winners.append(pid)
        
        return winners
        

class Poker(commands.Cog):
    def __init__(self, bot):
        print(f"⚠️ Poker Cog Loaded - ID: {id(self)}")
        self.bot = bot
        self.games = {} #channel_id: PokerGame
    
    @commands.command(name="텍사스")
    async def poker_main(self, ctx, action: str, amount:int = None):
        channel_id = ctx.channel.id

        if action == '규칙':
            try:
                await ctx.author.send(rules_text)
            except discord.Forbidden:
                await ctx.send("❌ DM을 보낼 수 없습니다. DM을 허용해주세요.")
        
        elif action == '시작':
            if channel_id in self.games:
                await ctx.send("이곳에서는 이미 게임이 진행 중입니다.")
                return
            
            self.games[channel_id] = PokerGame()
            await ctx.send("게임이 시작되었습니다! `-텍사스 참가`으로 참가하세요.")

        elif action == '참가':
            game = self.games.get(channel_id)
            if not game:
                return await ctx.send("게임이 아직 시작되지 않았습니다. `-텍사스 시작`을 먼저 입력하세요.")
            added = game.add_player(ctx.author)
            if added:
                await ctx.send(f"<@{ctx.author.id}> 님이 게임에 참가했습니다.")
            else:
                await ctx.send("이미 참가중이거나 게임이 시작되었습니다.")

        elif action == "배분":
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
            await ctx.send("카드가 배분되었습니다! 코인 베팅을 시작해주세요.")
            first_pid = game.betting.get_curr_player()
            await ctx.send(f"<@{first_pid}> 님의 차례입니다. 베팅해주세요.")


        elif action in ["베팅", "콜", "폴드"]:
            game = self.games.get(channel_id)
            if not game or not game.started:
                return await ctx.send("게임이 아직 시작되지 않았습니다.")
            
            player_id = ctx.author.id
            if player_id not in game.players:
                return await ctx.send("게임에 참가하지 않았습니다.")

            is_first_turn = game.betting.current_turn == 0

            if action == "폴드":
                game.betting.fold(player_id)
                await ctx.send(f"<@{player_id}> 님이 폴드했습니다.")
                if game.betting.only_one_left():
                    winner = game.betting.get_last_player()
                    await ctx.send(f"🎉 <@{winner}> 님이 모든 플레이어의 폴드로 승리했습니다!")

                    # Reveal all community cards
                    while len(game.community_cards) < 5:
                        game.community_cards.append(game.deck.pop())
                    await ctx.send(f"🃏 공유 카드: {' | '.join(game.community_cards)}")

                    # Distribute pot
                    coins = game.betting.load_coins()
                    coins[str(winner)] += game.betting.pot
                    game.betting.save_coins(coins)

                    await ctx.send(f"💰 <@{winner}> 님이 {game.betting.pot} 코인을 획득했습니다.")
                    del self.games[channel_id]
                    return
                elif game.betting.get_curr_player() == player_id:
                    # advance turn if folded player was the current turn
                    next_pid = game.betting.advance_turn()
                    await ctx.send(f"<@{next_pid}> 님의 차례입니다.")
                return  # Early return for 폴드

            # turn check only for 베팅 and 콜
            curr_player = game.betting.get_curr_player()
            if curr_player != player_id:
                return await ctx.send("당신의 차례가 아닙니다.")
            
            elif action == "콜":
                if is_first_turn:
                    return
                success, msg = game.betting.call(player_id)
                await ctx.send(f"<@{player_id}>: {msg}")
                if success:
                    game.betting.player_states[player_id]["has_acted"] = True
                    if game.betting.all_called_or_folded():
                        await ctx.send("베팅이 종료되었습니다.")
                        await ctx.send("다음 공유 카드를 열어주세요.")
                        return
                    else:
                        next_pid = game.betting.advance_turn()
                        await ctx.send(f"<@{next_pid}> 님의 차례입니다.")
            
            elif action == "베팅":
                if not is_first_turn:
                    return
                if game.betting.current_bet > 0:
                    return
                if amount is None:
                    return await ctx.send("사용법: `-텍사스 베팅 <금액>`")
                success, msg = game.betting.bet(player_id, amount)
                await ctx.send(f"<@{player_id}>: {msg}")
                if success:
                    game.betting.player_states[player_id]["has_acted"] = True
                    if game.betting.all_called_or_folded():
                        await ctx.send("베팅이 종료되었습니다.")
                        return
                    else:
                        next_pid = game.betting.advance_turn()
                        await ctx.send(f"<@{next_pid}> 님의 차례입니다.")
        
        elif action == "status":
            game = self.games.get(channel_id)
            if not game or not game.started:
                return await ctx.send("진행 중인 게임이 없습니다.")
            
            status = game.betting.get_status()
            pot = status["pot"]
            curr_bet = status["current_bet"]
            curr_player_id = status["turn_order"][status["current_turn"]]
            curr_player_mention = f"<@{curr_player_id}>"
            player_states = status["player_states"]

            status_lines = [
                f"**현재 판돈**: {pot} 코인",
                f"**현재 베팅 금액**: {curr_bet} 코인",
                f"**현재 차례**: {curr_player_mention}",
                f"**플레이어 상태**:"
            ]

            for pid in status["turn_order"]:
                state = player_states[pid]
                folded = "폴드됨" if not state["in_game"] else "참가중"
                status_lines.append(f"• <@{pid}>: {state['bet']} 코인 베팅 | {folded}")
            
            if game.community_cards:
                cards = " | ".join(game.community_cards)
                status_lines.append(f"**공유 카드**: {cards}")

            await ctx.send("\n".join(status_lines))
        
        elif action == "플랍":
            game = self.games.get(channel_id)
            if not game or not game.started:
                return await ctx.send("게임이 아직 시작되지 않았습니다.")
            if len(game.community_cards) >= 3:
                return await ctx.send("이미 플랍이 공개되었습니다.")
            if not game.betting.all_called_or_folded():
                return await ctx.send("아직 베팅이 끝나지 않았습니다.")
            game.flop()
            await ctx.send(f"🃏 공유 카드: {' | '.join(game.community_cards)}")
            await ctx.send("게임 속행 여부를 결정한 뒤 다음 카드를 공개해주세요.")

        elif action == "턴":
            game = self.games.get(channel_id)
            if not game or len(game.community_cards) < 3:
                return await ctx.send("먼저 플랍을 공개하세요.")
            if len(game.community_cards) >= 4:
                return await ctx.send("턴은 이미 공개되었습니다.")
            if not game.betting.all_called_or_folded():
                return await ctx.send("아직 베팅이 끝나지 않았습니다.")
            game.turn()
            cards = game.community_cards[:-1] + [f"***{game.community_cards[-1]}***"]
            await ctx.send(f"공유 카드: {' | '.join(cards)}")
            await ctx.send("게임 속행 여부를 결정한 뒤 다음 카드를 공개해주세요.")

        elif action == "리버":
            game = self.games.get(channel_id)
            if not game or len(game.community_cards) < 4:
                return await ctx.send("먼저 턴을 공개하세요.")
            if len(game.community_cards) == 5:
                return await ctx.send("리버는 이미 공개되었습니다.")
            game.river()
            cards = game.community_cards[:-1] + [f"***{game.community_cards[-1]}***"]
            await ctx.send(f"🃏 공유 카드: {' | '.join(cards)}")

            # End of the game
            await ctx.send("🪙 모든 공유 카드가 공개되었습니다.")
            winners = game.evaluate_winner()
            if winners:
                win_mentions = ", ".join(f"<@{w}>" for w in winners)
                await ctx.send(f"{win_mentions} 님의 승리!")
                pot_share = game.betting.pot // len(winners)
                coins = game.betting.load_coins()
                for w in winners:
                    coins[str(w)] += pot_share
                    await ctx.send(f"<@{w}> 님이 {pot_share} 코인을 획득했습니다.")
                game.betting.save_coins(coins)
            else:
                await ctx.send("⚠️ 승자를 판단할 수 없습니다.")
            del self.games[channel_id]
        
        elif action == "종료":
            game = self.games.get(channel_id)
            if not game:
                return await ctx.send("진행 중인 게임이 없습니다.")
            
            del self.games[channel_id]
            await ctx.send(f"<@{ctx.author.id}> 님의 요청으로 게임이 종료되었습니다.")


        else:
            await ctx.send("알 수 없는 명령어입니다. `텍사스 규칙`을 통해 사용 가능한 명령어를 확인하세요.")

async def setup(bot):
    await bot.add_cog(Poker(bot))
