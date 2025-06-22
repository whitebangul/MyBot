import json
import os

COINS_FILE = "data/coins.json"

class Betting:
    def __init__(self):
        self.pot = 0
        self.current_bet = 0
        self.turn_order = []
        self.player_states = {}  # {player_id: {"bet":0, "in_game": True, "has_acted": False}}
        self.current_turn = 0

    def load_coins(self):
        if os.path.exists(COINS_FILE):
            with open(COINS_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def save_coins(self, coins):
        with open(COINS_FILE, 'w') as f:
            json.dump(coins, f, indent=2)
    

    def setup_players(self, players):
        self.turn_order = list(players.keys())
        self.player_states = {
            pid: {"bet": 0, "round_bet": 0, "in_game": True, "has_acted": False}
            for pid in self.turn_order
        }
        self.current_bet = 0
        self.pot = 0
        self.current_turn = 0

    
    def get_curr_player(self):
        n = len(self.turn_order)
        for _ in range(n):
            pid = self.turn_order[self.current_turn]
            if self.player_states[pid]["in_game"]:
                return pid
            self.current_turn = (self.current_turn + 1) % n
        return None  # No active players left

    
    def advance_turn(self):
        n = len(self.turn_order)

        for _ in range(n):
            self.current_turn = (self.current_turn + 1) % n
            pid = self.turn_order[self.current_turn]
            if self.player_states[pid]["in_game"]:
                return pid
        return None
        
    def fold(self, pid):
        self.player_states[pid]["in_game"] = False
    
    def bet(self, pid, amt):
        coins = self.load_coins()
        if str(pid) not in coins or coins[str(pid)] < amt:
            return False, "코인이 부족합니다."
    
        coins[str(pid)] -= amt
        self.player_states[pid]["bet"] += amt
        self.player_states[pid]["round_bet"] += amt
        self.pot += amt
        self.current_bet = amt
        self.save_coins(coins)
        return True, f"{amt} 코인을 베팅했습니다."
    
    def call(self, pid):
        coins = self.load_coins()
        need = self.current_bet - self.player_states[pid]["round_bet"]

        if need <= 0:
            if self.player_states[pid].get("has_acted", False):
                return False, "이미 베팅했습니다."
            else:
                self.player_states[pid]["has_acted"] = True
                return True, "콜을 선언했습니다."
        if coins.get(str(pid), 0) < need:
            return False, "코인이 충분하지 않습니다."

        coins[str(pid)] -= need
        self.player_states[pid]["bet"] += need
        self.player_states[pid]["round_bet"] += need
        self.pot += need
        self.player_states[pid]["has_acted"] = True
        self.save_coins(coins)


        return True, "콜을 선언했습니다."

    def raise_bet(self, pid, raise_amt):
        if raise_amt <= 0:
            return False, "레이즈 금액은 2 코인 이상이어야 합니다."
        coins = self.load_coins()
        current = self.player_states[pid]["round_bet"]
        to_call = self.current_bet - current
        total = to_call + raise_amt
        
        if coins.get(str(pid), 0) < total:
            return False, "코인이 충분하지 않습니다."
        
        coins[str(pid)] -= total
        self.player_states[pid]["bet"] += total
        self.player_states[pid]["round_bet"] += total
        self.pot += total

        self.current_bet = self.player_states[pid]["round_bet"]

        self.player_states[pid]["has_acted"] = True

        for other_pid in self.turn_order:
            if other_pid != pid and self.player_states[other_pid]["in_game"]:
                self.player_states[other_pid]["has_acted"] = False
        
        self.save_coins(coins)
        return True, f"{raise_amt} 코인을 추가 베팅했습니다."
    
    def all_called_or_folded(self):
        active = [pid for pid in self.turn_order if self.player_states[pid]["in_game"]]
        return all(self.player_states[pid]["round_bet"] == self.current_bet and
                   self.player_states[pid]["has_acted"] for pid in active
                   )
    
    def only_one_left(self):
        active = [pid for pid in self.turn_order if self.player_states[pid]["in_game"]]
        return len(active) == 1

    def get_last_player(self):
        for pid in self.turn_order:
            if self.player_states[pid]["in_game"]:
                return pid
        return None

    def is_in_game(self, pid):
        return self.player_states.get(pid, {}).get("in_game", False)
    
    def get_status(self):
        return {
            "pot": self.pot,
            "current_bet": self.current_bet,
            "turn_order": self.turn_order,
            "player_states": self.player_states,
            "current_turn": self.current_turn
        }
    
    def reset_betting_round(self):
        self.current_turn = 0
        for pid in self.turn_order:
            self.player_states[pid]["has_acted"] = False
            self.player_states[pid]["round_bet"] = 0
