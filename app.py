from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import random
import os
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "replace-this-secret")
socketio = SocketIO(app, cors_allowed_origins="*")
@app.route("/")
def index():
    return "<h1>Blackjack Server is running!</h1>"

# ==================== BLACKJACK LOGIC ====================
def create_deck():
    suits = ["♠", "♥", "♦", "♣"]
    ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    deck = [r+s for s in suits for r in ranks]
    random.shuffle(deck)
    return deck

def card_value(card):
    rank = card[:-1]
    if rank == "J":
        return 11
    if rank == "Q":
        return 1
    if rank == "K":
        return 13
    if rank == "A":
        return 11
    return int(rank)

def hand_value(hand):
    value, aces = 0, 0
    for c in hand:
        v = card_value(c)
        value += v
        if c[:-1] == "A":
            aces += 1
    while value > 21 and aces > 0:
        value -= 10
        aces -= 1
    return value

def dealer_play(deck, hand):
    while hand_value(hand) < 17:
        hand.append(deck.pop())
    return hand

# ==================== ROUTES ====================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/solo", methods=["GET", "POST"])
def solo():
    if request.method == "POST":
        nickname = request.form.get("nickname", "Player1")
        deck = create_deck()
        player = [deck.pop(), deck.pop()]
        dealer = [deck.pop(), deck.pop()]
        dealer = dealer_play(deck, dealer)

        p_val, d_val = hand_value(player), hand_value(dealer)
        if p_val > 21 and d_val > 21:
            result = "Hòa (cả hai bust)"
        elif p_val > 21:
            result = "Bạn thua!"
        elif d_val > 21 or p_val > d_val:
            result = "Bạn thắng!"
        elif p_val == d_val:
            result = "Hòa!"
        else:
            result = "Bạn thua!"

        return render_template("solo.html", nickname=nickname,
                               player=player, p_val=p_val,
                               dealer=dealer, d_val=d_val,
                               result=result)
    return render_template("solo.html")

# ==================== PVP MODE ====================
rooms = {}

@app.route("/pvp")
def pvp():
    return render_template("pvp.html")

@socketio.on("join")
def handle_join(data):
    room = data["room"]
    nickname = data["nickname"]

    join_room(room)
    if room not in rooms:
        rooms[room] = {"players": [], "deck": create_deck()}
    rooms[room]["players"].append({"nickname": nickname, "hand": []})

    emit("status", {"msg": f"{nickname} đã vào phòng {room}"}, room=room)

@socketio.on("start_game")
def handle_start(data):
    room = data["room"]
    deck = rooms[room]["deck"]
    for player in rooms[room]["players"]:
        player["hand"] = [deck.pop(), deck.pop()]
    dealer = [deck.pop(), deck.pop()]
    rooms[room]["dealer"] = dealer

    emit("game_state", {"players": rooms[room]["players"], "dealer": dealer}, room=room)

# ==================== MAIN ====================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=False)
