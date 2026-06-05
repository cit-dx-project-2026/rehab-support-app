from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# メンバーのフロントエンド（HTMLファイル）からの非同期通信を許可する設定
CORS(app)

# 鈴木君が共通ルールで定めたAPIキー
VALID_API_KEY = "rehab-support-app-2026-key"

# 2. ログインをメール主軸に統一したため、テストアカウントのIDをメール形式に変更！
# データベースの代わりに、メモリ上にユーザー情報を保持（簡易実装）
USER_DATABASE = {
    "user@example.com": {
        "password": "password123",
        "username": "鈴木明輝"
    }
}

def check_api_key(headers):
    """共通のX-API-KEYヘッダーを検証する関数"""
    api_key = headers.get("X-API-KEY")
    return api_key == VALID_API_KEY

# ---------------------------------------------------
# 既存：ログインAPI（岩松君の要望に合わせてキーを email に変更！）
# ---------------------------------------------------
@app.route('/api/v1/login', methods=['POST'])  # 修正！
def login():
    if not check_api_key(request.headers):
        return jsonify({"status": "error", "message": "Invalid API Key"}), 401
    
    data = request.get_json() or {}
    # 岩松君への回答：キーを email に統一しました！
    email = data.get("email")
    password = data.get("password")
    
    if email in USER_DATABASE and USER_DATABASE[email]["password"] == password:
        return jsonify({
            "status": "success",
            "user_id": email,  # 共通app.jsのsaveLoginInfoに渡す一意のID（メールアドレス）
            "username": USER_DATABASE[email]["username"],
            "message": "ログインに成功しました。"
        }), 200
    else:
        return jsonify({
            "status": "error",
            "message": "メールアドレスまたはパスワードが間違っています。"
        }), 401

# ---------------------------------------------------
# 新設：1. 新規登録API（最優先要望）
# ---------------------------------------------------
@app.route('/api/v1/register', methods=['POST'])  # 修正！
def register():
    if not check_api_key(request.headers):
        return jsonify({"status": "error", "message": "Invalid API Key"}), 401
    
    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    
    if not username or not email or not password:
        return jsonify({"status": "error", "message": "入力項目が不足しています。"}), 400
        
    if email in USER_DATABASE:
        return jsonify({"status": "error", "message": "このメールアドレスは既に登録されています。"}), 400
        
    # 新しいユーザーをデータベース（もどき）に追加
    USER_DATABASE[email] = {
        "password": password,
        "username": username
    }
    
    return jsonify({
        "status": "success",
        "user_id": email,
        "message": "アカウントの作成に成功しました。"
    }), 200

# ---------------------------------------------------
# 新設：1. パスワード再設定API（最優先要望）
# ---------------------------------------------------
@app.route('/api/v1/password-reset', methods=['POST'])  # 修正！
def password_reset():
    if not check_api_key(request.headers):
        return jsonify({"status": "error", "message": "Invalid API Key"}), 401
        
    data = request.get_json() or {}
    email = data.get("email")
    new_password = data.get("new_password")
    
    if not email or not new_password:
        return jsonify({"status": "error", "message": "入力項目が不足しています。"}), 400
        
    if email not in USER_DATABASE:
        return jsonify({"status": "error", "message": "登録されていないメールアドレスです。"}), 404
        
    # パスワードを更新
    USER_DATABASE[email]["password"] = new_password
    
    return jsonify({
        "status": "success",
        "message": "パスワードの再設定が完了しました。"
    }), 200

if __name__ == '__main__':
    # 開発環境用にポート5000番で起動
    app.run(debug=True, port=5000)