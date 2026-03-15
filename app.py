# -*- coding: utf-8 -*-
from flask import Flask, render_template, session, request, jsonify, send_from_directory, Response
import random

app = Flask(__name__)
app.secret_key = "ctf_stage2_secret_key_x9z"

# ── Obfuscated asset routes — hides real filenames from HTML source ──────────
@app.route("/assets/v2/runtime.js")
def serve_js():
    resp = send_from_directory("static", "ui-core.min.js", mimetype="application/javascript")
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp

@app.route("/assets/v2/runtime.css")
def serve_css():
    resp = send_from_directory("static", "theme.min.css", mimetype="text/css")
    resp.headers["Cache-Control"] = "no-store"
    return resp

DEAD_SYMBOL = "\U0001f4a0"   # 💠 — 25th decorative card, pre-disabled
SYMBOLS = [
    "\u26a1",      # ⚡
    "\U0001f510",  # 🔐
    "\U0001f4be",  # 💾
    "\U0001f9e0",  # 🧠
    "\U0001f6f0",  # 🛰️
    "\U0001f50e",  # 🔎
    "\U0001f9ec",  # 🧬
    "\U0001f9e9",  # 🧩
    "\U0001f5dd",  # 🗝️
    "\U0001f4bb",  # 💻
    "\U0001f4e1",  # 📡
    "\U0001f50b",  # 🔋
]

# Valid credentials — backend only, never sent to frontend
VALID_EMAIL    = "ross.thompson94@example.com"
VALID_PASSWORD = "R0ss!Secure829"
VALID_COUPON   = "TRACECTF{RGlsIG1hbmdlIG1vcmUgZ2FtZXM=}"
FINAL_FLAG     = "TRACECTF{Dil mange more games}"

def generate_board():
    # 12 pairs (24 cards) + 1 DEAD card = 25
    cards = SYMBOLS * 2        # 24
    cards += [DEAD_SYMBOL]     # 25
    random.shuffle(cards)
    return cards

@app.route("/")
def index():
    session.clear()
    board = generate_board()
    session["board"]             = board
    session["matched"]           = [board.index(DEAD_SYMBOL)]  # dead card pre-matched
    session["shuffle_disabled"]  = False   # disabled after first successful match
    session["game_won"]          = False
    return render_template("index.html")

@app.route("/get_board", methods=["GET"])
def get_board():
    return jsonify({
        "board_size":       len(session.get("board", [])),
        "matched":          session.get("matched", []),
        "shuffle_disabled": session.get("shuffle_disabled", False),
    })

@app.route("/flip_card", methods=["POST"])
def flip_card():
    data    = request.get_json()
    idx     = data.get("index")
    board   = session.get("board", [])
    matched = session.get("matched", [])
    if idx is None or idx < 0 or idx >= len(board) or idx in matched:
        return jsonify({"error": "invalid"}), 400
    return jsonify({"symbol": board[idx]})

@app.route("/check_pair", methods=["POST"])
def check_pair():
    data    = request.get_json()
    idx1    = data.get("index1")
    idx2    = data.get("index2")
    board   = session.get("board", [])
    matched = session.get("matched", [])
    shuffle_disabled = session.get("shuffle_disabled", False)

    if idx1 is None or idx2 is None:
        return jsonify({"error": "invalid"}), 400
    if idx1 == idx2:
        return jsonify({"match": False, "scramble": not shuffle_disabled})

    sym1 = board[idx1]
    sym2 = board[idx2]

    if sym1 != sym2:
        if not shuffle_disabled:
            unmatched = [i for i in range(len(board)) if i not in matched]
            syms = [board[i] for i in unmatched]
            random.shuffle(syms)
            for i, idx in enumerate(unmatched):
                board[idx] = syms[i]
            session["board"] = board
            session.modified = True
            return jsonify({"match": False, "scramble": True})
        return jsonify({"match": False, "scramble": False})

    # It's a match
    matched += [idx1, idx2]
    session["matched"] = matched
    response = {"match": True, "scramble": False, "symbol": sym1}

    # First ever match — disable shuffle permanently
    if not shuffle_disabled:
        session["shuffle_disabled"] = True
        response["first_match"] = True
        response["corner_message"] = "Memory fragments stabilised. Shuffle disabled."

    # Win condition: all 24 matchable cards matched (dead card is pre-matched)
    if len(matched) >= len(board) and not session.get("game_won", False):
        session["game_won"] = True
        response["game_won"] = True

    session.modified = True
    return jsonify(response)

@app.route("/login", methods=["POST"])
def login():
    data     = request.get_json()
    email    = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()
    if email == VALID_EMAIL and password == VALID_PASSWORD:
        coupon = "TRACECTF{RGlsIG1hbmdlIG1vcmUgZ2FtZXM=}"
        return jsonify({"success": True, "coupon": coupon})
    return jsonify({"success": False, "message": "Invalid credentials. Try again."})

@app.route("/redeem_coupon", methods=["POST"])
def redeem_coupon():
    data   = request.get_json()
    coupon = (data.get("coupon") or "").strip()
    if coupon == VALID_COUPON:
        return jsonify({"success": True, "flag": FINAL_FLAG})
    return jsonify({"success": False, "message": "Invalid coupon code."})

@app.route("/restart", methods=["POST"])
def restart():
    session.clear()
    board = generate_board()
    session["board"]             = board
    session["matched"]           = [board.index(DEAD_SYMBOL)]
    session["shuffle_disabled"]  = False
    session["game_won"]          = False
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(debug=False)
