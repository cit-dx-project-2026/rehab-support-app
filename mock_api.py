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
    # データベースから該当するユーザーを探索
    user = conn.execute("SELECT * FROM users WHERE email = ? AND password = ?;", (email, password)).fetchone()
    
    if user:
        # 💡鈴木追加ロジック：ログインが成功したら、ログイン管理テーブルの情報を取得・判定する
        login_info = conn.execute("SELECT * FROM login_management WHERE email = ?;", (email,)).fetchone()
        
        # 今日（当日の日付文字列 例: "2026-06-20"）を取得
        today_str = datetime.date.today().isoformat()
        
        if login_info:
            last_login = login_info['last_login_date']
            current_days = login_info['login_days']
            
            # 【重要：連続ログイン日数の本物計算ロジック】
            if last_login == today_str:
                # 同日中の2回目以降のログイン ➔ 日数は据え置き
                pass
            elif last_login == (datetime.date.today() - datetime.timedelta(days=1)).isoformat():
                # 前日からの連続ログイン ➔ 日数を+1更新
                current_days += 1
                conn.execute("UPDATE login_management SET login_days = ?, last_login_date = ? WHERE email = ?;", 
                             (current_days, today_str, email))
            else:
                # 日が空いてしまった場合、または新規 ➔ 日数を1にリセット
                current_days = 1
                conn.execute("UPDATE login_management SET login_days = ?, last_login_date = ? WHERE email = ?;", 
                             (current_days, today_str, email))
        else:
            # ログイン管理レコード自体がなければ新しく作成（1日目としてカウント）
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
    
    # 既に同じメールアドレスが登録されていないか重複チェック
    existing_user = conn.execute("SELECT * FROM users WHERE email = ?;", (email,)).fetchone()
    if existing_user:
        conn.close()
        return jsonify({"message": "このメールアドレスは既に登録されています。"}), 409

    try:
        # 1. ユーザー情報テーブルに挿入
        conn.execute("INSERT INTO users (email, password, username) VALUES (?, ?, ?);", 
                     (email, password, username))
        
        # 2. ログイン管理テーブルの初期レコードも一緒に作っておく（初期日数0）
        conn.execute("INSERT INTO login_management (email, login_days, last_login_date, input_today_flag) VALUES (?, 0, NULL, 0);",
                     (email,))
        
        # 3. 新規特典データの初期セット（ロックされた状態）を自動生成
        conn.executemany("""
        INSERT INTO incentives (email, incentive_type, status, required_days, expire_date, shop_name)
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
# ===============================================================
@app.route('/api/v1/password-reset', methods=['POST'])
def password_reset():
    if not check_api_key():
        return jsonify({"message": "Invalid API Key"}), 401

    data = request.json or {}
    email = data.get("email")
    new_password = data.get("new_password")

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?;", (email,)).fetchone()
    
    if not user:
        conn.close()
        return jsonify({"message": "このメールアドレスは登録されていません。"}), 404

    conn.execute("UPDATE users SET password = ? WHERE email = ?;", (new_password, email))
    conn.commit()
    conn.close()
    
    print(f"[DB SUCCESS] パスワード再設定完了: {email}")
    return jsonify({"message": "Password updated successfully"}), 200

if __name__ == '__main__':
    # サーバー起動
    app.run(host='127.0.0.1', port=5000, debug=True)