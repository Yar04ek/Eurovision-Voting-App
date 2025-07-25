import os, json, datetime
from pathlib import Path
from functools import wraps
from flask import Flask, jsonify, request, render_template, redirect, url_for, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

# ─── Пути и файлы ───────────────────────────────────────────────
BASE_DIR        = Path(__file__).parent
DATA_DIR        = BASE_DIR / "data"; DATA_DIR.mkdir(exist_ok=True)
ART_FILE        = DATA_DIR / "artists.json"
USERS_FILE      = DATA_DIR / "users.json"
VOTES_FILE      = DATA_DIR / "votes.json"
GRAND_FILE      = DATA_DIR / "grand_final.json"
GRAND_VOTES_FILE= DATA_DIR / "grand_votes.json"      # ← новый

def load_json(path, default):
    if not path.exists() or not path.read_text(encoding='utf-8').strip():
        path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding='utf-8')
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding='utf-8')
        return default

def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

# данные
artists     = load_json(ART_FILE, [])
users       = load_json(USERS_FILE, {})
votes       = load_json(VOTES_FILE, {})
grand_final = load_json(GRAND_FILE, [])
grand_votes = load_json(GRAND_VOTES_FILE, {})    # ← загрузили

# конвертация старого формата users
for login, meta in list(users.items()):
    if isinstance(meta, str):
        users[login] = {"pw": meta, "admin": False}

# инициализация артистов
for idx, art in enumerate(artists, 1):
    art.setdefault("id", idx)
    art.setdefault("semi_final", art.get("semi_final", art.get("semi", 0)))
    art.setdefault("performance_order", art.get("performance_order", idx))
    art.setdefault("official_final", art.get("official_final", False))

# ─── Flask ──────────────────────────────────────────────────────
app = Flask(__name__, static_folder="static", template_folder="templates")
app.config.update({
    "SECRET_KEY":            os.getenv("SECRET_KEY", "dev_secret"),
    "JWT_SECRET_KEY":        os.getenv("SECRET_KEY", "dev_secret"),
    "JWT_ACCESS_TOKEN_EXPIRES": datetime.timedelta(days=7)
})
jwt = JWTManager(app)

def is_admin(login):
    return users.get(login, {}).get("admin", False)

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        if not is_admin(get_jwt_identity()):
            return jsonify(msg="for admin only"), 403
        return fn(*args, **kwargs)
    return wrapper

# ─── HTML-маршруты ───────────────────────────────────────────────
@app.route("/")
def index(): return render_template("index.html")

@app.route("/grand-results-page")                # ← НОВЫЙ роут для результатов финала
def grand_results_page():
    return render_template("grand_results_page.html")

@app.route("/register")
def register_page(): return render_template("register.html")

@app.route("/dashboard")
def dashboard(): return render_template("dashboard.html")

@app.route("/semi-final/<int:n>")
def semi_final(n): return render_template("semi_final.html", semi=n)

@app.route("/final-page")
def final_page(): return render_template("final_page.html")

@app.route("/results-page")
def results_page(): return render_template("results_page.html")

@app.route("/logout")
def logout(): return redirect(url_for("index"))

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(app.static_folder, "images/Eurovision_Song_Contest_2025_Logo.jpg")

# ─── Auth API ────────────────────────────────────────────────────
@app.post("/api/register")
def api_register():
    data  = request.get_json() or {}
    login = data.get("login","").strip().lower(); pwd = data.get("password","")
    if not login or not pwd:
        return jsonify(msg="login & password required"),400
    if login in users:
        return jsonify(msg="login exists"),409
    users[login] = {
        "pw":    generate_password_hash(pwd, method="pbkdf2:sha256", salt_length=16),
        "admin": False,
    }
    votes[login] = {}
    save_json(USERS_FILE, users)
    save_json(VOTES_FILE, votes)
    return jsonify(msg="registered"),201

@app.post("/api/login")
def api_login():
    data  = request.get_json() or {}
    login = data.get("login","").strip().lower(); pwd = data.get("password","")
    meta  = users.get(login)
    if not meta or not check_password_hash(meta["pw"], pwd):
        return jsonify(msg="bad creds"),401
    token = create_access_token(identity=login)
    return jsonify(access_token=token),200

def merge_votes(login):
    user_votes = votes.get(login, {})
    out = []
    for art in artists:
        uv = user_votes.get(str(art["id"]), {})
        out.append({
            "id":   art["id"],
            "name": art["name"],
            "semi": art["semi_final"],
            "order": art["performance_order"],
            "score": uv.get("score"),
            "final": uv.get("final", False),
            "official": art.get("official_final", False)
        })
    return out

@app.get("/api/semi-finals/<int:n>")
@jwt_required()
def api_semi(n):
    login = get_jwt_identity()
    data  = [a for a in merge_votes(login) if a["semi"]==n]
    data.sort(key=lambda x: x["order"])
    return jsonify(admin=is_admin(login), artists=data)

# ─── Эндпоинт гран-финала (список участников) ─────────────────
@app.get("/api/grand-final")
@jwt_required()
def api_grand_final():
    login      = get_jwt_identity()
    gf_entries = load_json(GRAND_FILE, [])
    user_votes = grand_votes.get(login, {})

    finalists = []
    for entry in gf_entries:
        # вычисляем ID и доп. поля
        if isinstance(entry, (int, str)) and str(entry).isdigit():
            aid, extra = int(entry), {}
        elif isinstance(entry, dict) and "id" in entry:
            aid, extra = int(entry["id"]), entry
        else:
            continue

        base = next((a for a in artists if a["id"] == aid), None)
        if not base: continue

        card = {**base, **extra, "official_final": True}
        uv   = user_votes.get(str(aid), {})

        finalists.append({
            "id":    card["id"],
            "name":  card["name"],
            "order": card.get("performance_order", 999),
            "score": uv.get("score"),
            "final": uv.get("final", False),
            "official": True
        })
    # сортируем по ID (или по order, как вам удобнее)
    finalists.sort(key=lambda x: x["id"])
    return jsonify(admin=is_admin(login), artists=finalists)

# ─── Новая запись голосов гран-финала ─────────────────────────
@app.post("/api/grand-vote")
@jwt_required()
def api_grand_vote():
    login = get_jwt_identity()
    p     = request.get_json() or {}
    aid   = str(p.get("artist_id"))
    if not aid:
        return jsonify(msg="artist_id required"),400

    gv    = grand_votes.setdefault(login, {})
    entry = gv.setdefault(aid, {})
    if "score" in p: entry["score"] = p["score"]
    if "final" in p: entry["final"] = bool(p["final"])
    save_json(GRAND_VOTES_FILE, grand_votes)
    return jsonify(msg="saved")

# ─── Голосование за полуфиналистов ─────────────────────────────
@app.post("/api/vote")
@jwt_required()
def api_vote():
    login = get_jwt_identity()
    p     = request.get_json() or {}
    aid   = str(p.get("artist_id"))
    if not aid:
        return jsonify(msg="artist_id required"),400
    uv    = votes.setdefault(login, {})
    entry = uv.setdefault(aid, {})
    if "score" in p: entry["score"] = p["score"]
    if "final" in p: entry["final"] = bool(p["final"])
    save_json(VOTES_FILE, votes)
    return jsonify(msg="saved")
# ─── ADMIN: переключаем official_final и синхронизируем grand_final.json ─────────
@app.post("/api/admin/final/<int:aid>")
@admin_required
def admin_toggle(aid):
    art = next((a for a in artists if a["id"]==aid), None)
    if not art: return jsonify(msg="not found"),404
    art["official_final"] = not art.get("official_final",False)
    save_json(ART_FILE, artists)

    gf = load_json(GRAND_FILE, [])
    gf = [x for x in gf if not ((isinstance(x,int) and x==aid)
                               or (isinstance(x,dict) and x.get("id")==aid))]
    if art["official_final"]:
        gf.append({
            "id":                art["id"],
            "name":              art["name"],
            "semi_final":        art["semi_final"],
            "performance_order": art["performance_order"],
            "official_final":    True
        })
    save_json(GRAND_FILE, gf)
    return jsonify(official=art["official_final"])

@app.put("/api/admin/final/order/<int:aid>")
@admin_required
def admin_order(aid):
    d    = (request.get_json() or {}).get("direction")
    line = [a for a in artists if a.get("official_final")]
    line.sort(key=lambda x: x["performance_order"])
    idx  = next((i for i,a in enumerate(line) if a["id"]==aid),None)
    if idx is None: return jsonify(msg="not in final"),404
    if d=="up"   and idx>0:        line[idx]["performance_order"], line[idx-1]["performance_order"] = \
                                    line[idx-1]["performance_order"], line[idx]["performance_order"]
    if d=="down" and idx<len(line)-1: line[idx]["performance_order"], line[idx+1]["performance_order"] = \
                                    line[idx+1]["performance_order"], line[idx]["performance_order"]
    save_json(ART_FILE, artists)
    return jsonify(msg="ok")

# ─── Страница результатов гран-финала ─────────────────────────
@app.route("/results-final-page")
def results_final_page():
    return render_template("results_final.html")

# ─── Эндпоинт результатов гран-финала ─────────────────────────
@app.get("/api/results-final")
@jwt_required()
def api_results_final():
    gf_entries = load_json(GRAND_FILE, [])
    # кто участвует
    gf_ids = []
    for e in gf_entries:
        if isinstance(e,(int,str)) and str(e).isdigit():
            gf_ids.append(int(e))
        elif isinstance(e,dict) and "id" in e:
            gf_ids.append(int(e["id"]))

    # сводка голосов только по гран-финалистам
    summary = {}
    for usr, uv in grand_votes.items():
        for aid_str, v in uv.items():
            aid = int(aid_str)
            if aid not in gf_ids: continue
            stats = summary.setdefault(aid, {"scores":[], "finals":0, "voters":[]})
            if v.get("score") is not None: stats["scores"].append(v["score"])
            if v.get("final"):             stats["finals"] += 1
            if v:                           stats["voters"].append(usr)

    # собираем ответ
    out = []
    for e in gf_entries:
        # та же логика по id/extra
        if isinstance(e,(int,str)) and str(e).isdigit():
            aid, extra = int(e), {}
        elif isinstance(e,dict) and "id" in e:
            aid, extra = int(e["id"]), e
        else:
            continue
        base = next((a for a in artists if a["id"]==aid), None)
        if not base: continue
        card = {**base, **extra}
        stats = summary.get(aid, {"scores":[], "finals":0, "voters":[]})
        avg   = None if not stats["scores"] else round(sum(stats["scores"])/len(stats["scores"]),2)

        out.append({
            "order":        card.get("performance_order", aid),
            "name":         card["name"],
            "avg":          avg,
            "final_votes":  stats["finals"],
            "voters":       stats["voters"]
        })
    out.sort(key=lambda x: x["order"] if x["order"] is not None else float('inf'))
    return jsonify(out)

# ─── Эндпоинт результатов обычных полу/финалов ───────────────────
@app.get("/api/results")
@jwt_required()
def api_results():
    summary = {}
    for usr, uv in votes.items():
        for aid, v in uv.items():
            s = summary.setdefault(aid, {"scores":[], "finals":0, "voters":[]})
            if v.get("score") is not None: s["scores"].append(v["score"])
            if v.get("final"):            s["finals"] += 1
            if v:                         s["voters"].append(usr)
    out = []
    for art in artists:
        aid = str(art["id"]); s = summary.get(aid, {})
        avg = None if not s.get("scores") else round(sum(s["scores"])/len(s["scores"]),2)
        out.append({
            "order": art["performance_order"],
            "name":  art["name"],
            "avg":   avg,
            "final_votes": s.get("finals",0),
            "voters": s.get("voters",[])
        })
    out.sort(key=lambda x: x["order"] if x["order"] is not None else float('inf'))
    return jsonify(out)


if __name__=="__main__":
    app.run(debug=False)
