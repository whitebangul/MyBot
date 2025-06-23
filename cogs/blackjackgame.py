from discord.ext import commands
from .bettings import Betting
import random

SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

def create_deck():
    return [f"{rank}{suit}" for suit in SUITS for rank in RANKS]

class BlackJackGame:
    def __init__(self, user_id):
        self.user_id = user_id
        self.deck = create_deck()
        random.shuffle(self.deck)
        self.player_hand = [self.deck.pop(), self.deck.pop()]
        self.dealer_hand = [self.deck.pop(), self.deck.pop()]  # face up, face down
        self.game_over = False
        self.result = None
        self.bet = 0
        self.betting = Betting()

    def calculate_hand_value(self, hand):
        value = 0
        num_aces = 0

        for card in hand:
            rank = card[:-1]
            if rank in ['J', 'Q', 'K']:  # face cards
                value += 10
            elif rank == 'A':
                num_aces += 1
                value += 11
            else:  # number value
                value += int(rank)
        while value > 21 and num_aces:
            value -= 10
            aces -= 1
        return value
    
    def get_player_value(self):
        return self.calculate_hand_value(self.player_hand)
    
    def get_dealer_value(self):
        return self.calculate_hand_value(self.dealer_hand)

    def place_bet(self, amt):
        if self.bet > 0:
            return False, "이미 베팅하셨습니다."
        if amt < 1 or amt > 5:
            return False, "최소 1코인, 최대 5코인 베팅 가능합니다."
        coins = self.betting.load_coins()
        pid = str(self.user_id)
        if pid not in coins or coins[pid] < amt:
            return False, "코인이 부족합니다."
        coins[pid] -= amt
        self.betting.save_coins(coins)
        self.bet = amt
        return True, f"{amt} 코인을 베팅했습니다."
    
    def hit(self):
        if self.game_over or self.bet == 0:
            return "카드를 받을 수 없습니다."
        self.player_hand.append(self.deck.pop())
        if self.get_player_value() > 21:
            self.game_over = True
            return self.end_game()
        return None

    def stand(self):
        if self.game_over or self.bet == 0:
            return "카드를 공개할 수 없습니다."
        while self.get_dealer_value() < 17:
            self.dealer_hand.append(self.deck.pop())
        self.game_over = True
        return self.end_game()
    
    def end_game(self):
        coins = self.betting.load_coins()
        pid = str(self.user_id)
        player = self.get_player_value()
        dealer = self.get_dealer_value()

        if player > 21:
            self.result = f"**버스트! 당신의 패배입니다.** `(-{self.bet} 코인)`"
        elif dealer > 21 or player > dealer:
            coins[pid] += self.bet * 2
            self.result = f"**당신의 승리입니다.** `(+{self.bet * 2} 코인)`"
        elif player < dealer:
            self.result = f"**도박꾼의 승리입니다.** `(-{self.bet} 코인)`"
        else:
            coins[pid] += self.bet
            self.result = f"**비겼습니다.** `(코인 변화 없음)`"
        
        self.betting.save_coins(coins)
        return self.result
    
    def is_game_over(self):
        return self.game_over
    
    def get_hands(self, reveal_dealer=False):
        dealer_display = (
            ", ".join(self.dealer_hand)
            if reveal_dealer or self.game_over
            else f"{self.dealer_hand[0]}, ??"
        )
        return (
            f"**당신의 카드:** {', '.join(self.player_hand)} "
            f"(총합: {self.get_player_value()})\n"
            f"**도박꾼의 카드:** {dealer_display} "
            f"{'(총합: ' + str(self.get_dealer_value()) + ')' if reveal_dealer or self.game_over else ''}"
        )
