from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import datetime

app = Flask(__name__)
CORS(app)  # フロントエンドからの通信（クロスドメイン）を許可

DB_NAME = "rehab_app.db"
API_KEY = "rehab-support-app-2026-key"

# 共通：APIキーのチェックヘルパー
def check_api_key():
    return request.headers.get("X-API-KEY") == API_KEY

# 共通：データベース接続ヘルパー
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # 列名でデータを取得できるようにする
    return conn

# ===============================================================
# 1. ログイン API (POST /api/v1/login)
# ===============================================================
@app.route('/api/v1/login', methods=['POST'])
def login():
    if not check_api_key():
        return jsonify({"message": "Invalid API Key"}), 401

    data = request.json or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "メールアドレスとパスワードを入力してください。"}), 400

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ? AND password = ?;", (email, password)).fetchone()
    
    if user:
        login_info = conn.execute("SELECT * FROM login_management WHERE email = ?;", (email,)).fetchone()
        today_str = datetime.date.today().isoformat()
        
        if login_info:
            last_login = login_info['last_login_date']
            current_days = login_info['login_days']
            
            # 【重要：連続ログイン日数の本物計算＆日付変更時リセットロジック】
            if last_login == today_str:
                # 同日中の2回目以降のログイン ➔ 日数も入力フラグも据え置き（何もしない）
                pass
            elif last_login == (datetime.date.today() - datetime.timedelta(days=1)).isoformat():
                # 💡鈴木修正：前日からの連続ログイン時、日数を+1し、かつ「本日入力フラグ」を確実に 0 にリセット！
                current_days += 1
                conn.execute("UPDATE login_management SET login_days = ?, last_login_date = ?, input_today_flag = 0 WHERE email = ?;", 
                             (current_days, today_str, email))
            else:
                # 💡鈴木修正：日が空いてしまった場合、日数を1に戻し、かつ「本日入力フラグ」を確実に 0 にリセット！
                current_days = 1
                conn.execute("UPDATE login_management SET login_days = ?, last_login_date = ?, input_today_flag = 0 WHERE email = ?;", 
                             (current_days, today_str, email))
        else:
            # ログイン管理レコード自体がなければ新しく作成（1日目としてカウント、未入力状態0からスタート）
            conn.execute("INSERT INTO login_management (email, login_days, last_login_date, input_today_flag) VALUES (?, 1, ?, 0);",
                         (email, today_str))
            
        conn.commit()
        conn.close()
        
        print(f"[DB SUCCESS] ログイン成功: {email}")
        return jsonify({
            "message": "Login successful",
            "user_id": email,
            "username": user["username"]
        }), 200
    else:
        conn.close()
        return jsonify({"message": "メールアドレスまたはパスワードが正しくありません。"}), 401

# ===============================================================
# 2. 新規会員登録 API (POST /api/v1/register)
# ===============================================================
@app.route('/api/v1/register', methods=['POST'])
def register():
    if not check_api_key():
        return jsonify({"message": "Invalid API Key"}), 401

    data = request.json or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"message": "すべての項目を入力してください。"}), 400

    conn = get_db_connection()
    
    existing_user = conn.execute("SELECT * FROM users WHERE email = ?;", (email,)).fetchone()
    if existing_user:
        conn.close()
        return jsonify({"message": "このメールアドレスは既に登録されています。"}), 409

    try:
        conn.execute("INSERT INTO users (email, password, username) VALUES (?, ?, ?);", 
                     (email, password, username))
        
        conn.execute("INSERT INTO login_management (email, login_days, last_login_date, input_today_flag) VALUES (?, 0, NULL, 0);",
                     (email,))
        
        conn.executemany("""
        INSERT INTO incentive (email, incentive_type, status, required_days, expire_date, shop_name)
        VALUES (?, ?, ?, ?, ?, ?);
        """, [
            (email, "ジュース無料券", "locked", 7, "残り7日", "◯◯温泉"),
            (email, "マッサージチェア30分券", "locked", 14, "あと2日", "◯◯ドラッグストア")
        ])
        
        conn.commit()
        print(f"[DB SUCCESS] 新規ユーザー登録完了: {email}")
        return jsonify({"message": "User registered successfully", "user_id": email}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"登録中にエラーが発生しました: {str(e)}"}), 500
    finally:
        conn.close()

# ===============================================================
# 3. パスワード再設定 API (POST /api/v1/password-reset)
# 💡壊れて消失していたデコレータと関数定義を完全に復元して分離しました！
# ===============================================================
@app.route('/api/v1/password-reset', methods=['POST'])
def password_reset():
    if not check_api_key():
        return jsonify({"message": "Invalid API Key"}), 401

    data = request.json or {}
    email = data.get("email")
    new_password = data.get("new_password")

    if not email or not new_password:
        return jsonify({"message": "必要なデータが不足しています。"}), 400

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?;", (email,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"message": "ユーザーが見つかりません。"}), 404

    conn.execute("UPDATE users SET password = ? WHERE email = ?;", (new_password, email))
    conn.commit()
    conn.close()
    
    print(f"[DB SUCCESS] パスワード再設定完了: {email}")
    return jsonify({"message": "Password updated successfully"}), 200

# ===============================================================
# 4. ログインステータス取得 API (GET /api/v1/login-status)
# ===============================================================
@app.route('/api/v1/login-status', methods=['GET'])
def get_login_status():
    if not check_api_key():
        return jsonify({"message": "Invalid API Key"}), 401

    email = request.args.get("user_id")
    if not email:
        return jsonify({"message": "user_idが必要です。"}), 400

    conn = get_db_connection()
    login_info = conn.execute("SELECT * FROM login_management WHERE email = ?;", (email,)).fetchone()
    conn.close()

    if login_info:
        return jsonify({
            "user_id": email,
            "login_days": login_info["login_days"],
            "input_today_flag": bool(login_info["input_today_flag"]),
            "last_login_date": login_info["last_login_date"]
        }), 200
    else:
        return jsonify({"login_days": 0, "input_today_flag": False}), 200

# ===============================================================
# 5. 日次記録保存 API (POST /api/v1/daily-record)
# ===============================================================
@app.route('/api/v1/daily-record', methods=['POST'])
def save_daily_record():
    if not check_api_key():
        return jsonify({"message": "Invalid API Key"}), 401

    data = request.json or {}
    email = data.get("user_id")
    record_date = data.get("record_date")
    mood = data.get("mood")
    condition = data.get("condition")
    outing = data.get("outing")
    purpose = data.get("purpose", "")
    sleep = data.get("sleep")
    bed_time = data.get("bed_time")
    wake_time = data.get("wake_time")

    if not email or not record_date:
        return jsonify({"message": "user_id と record_date は必須です。"}), 400

    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT OR REPLACE INTO daily_records 
            (email, record_date, mood, condition, outing, purpose, sleep, bed_time, wake_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (email, record_date, mood, condition, outing, purpose, sleep, bed_time, wake_time))
        
        conn.execute("UPDATE login_management SET input_today_flag = 1 WHERE email = ?;", (email,))
        
        conn.commit()
        print(f"[DB SUCCESS] 日次記録保存完了: {email} ({record_date})")
        return jsonify({"message": "Daily record saved successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"保存エラー: {str(e)}"}), 500
    finally:
        conn.close()

# ===============================================================
# 6. 日次記録一覧取得 API (GET /api/v1/daily-records)
# ===============================================================
@app.route('/api/v1/daily-records', methods=['GET'])
def get_daily_records():
    if not check_api_key():
        return jsonify({"message": "Invalid API Key"}), 401

    email = request.args.get("user_id")
    if not email:
        return jsonify({"message": "user_idが必要です。"}), 400

    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM daily_records WHERE email = ?;", (email,)).fetchall()
    conn.close()

    records_dict = {}
    for row in rows:
        mood_num = str(row["mood"])
        emoji_map = {"5": "😆", "4": "😊", "3": "😐", "2": "😞", "1": "😢"}
        emoji = emoji_map.get(mood_num, "😐")

        records_dict[row["record_date"]] = {
            "mood": mood_num,
            "emoji": emoji,
            "condition": row["condition"],
            "outing": row["outing"],
            "sleep": row["sleep"],
            "times": f"就寝 {row['bed_time']} / 起床 {row['wake_time']}"
        }

    return jsonify(records_dict), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)