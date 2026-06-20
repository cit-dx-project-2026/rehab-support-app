import sqlite3
import os

def init_database():
    db_name = "rehab_app.db"
    
    # 既存の古いDBがあれば削除して綺麗に作り直す（テスト用）
    if os.path.exists(db_name):
        os.remove(db_name)
        print(f"既存の {db_name} を削除しました。新しく作り直します。")

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # 外部キー制約を有効化
    cursor.execute("PRAGMA foreign_keys = ON;")

    print("テーブルの作成を開始します...")

    # 1. ユーザー情報テーブル
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        username TEXT NOT NULL,
        created_at DATETIME NOT NULL DEFAULT (DATETIME('now', 'localtime'))
    );
    """)

    # 2. ログイン管理テーブル
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS login_management (
        email TEXT PRIMARY KEY,
        login_days INTEGER NOT NULL DEFAULT 0,
        last_login_date TEXT,
        input_today_flag BOOLEAN NOT NULL DEFAULT 0,
        FOREIGN KEY (email) REFERENCES users (email) ON DELETE CASCADE
    );
    """)

    # 3. 日次記録テーブル（SQLite仕様の AUTOINCREMENT に修正）
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_records (
        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        record_date TEXT NOT NULL,
        mood INTEGER NOT NULL,
        condition TEXT NOT NULL,
        outing TEXT NOT NULL,
        purpose TEXT,
        sleep TEXT NOT NULL,
        bed_time TEXT NOT NULL,
        wake_time TEXT NOT NULL,
        FOREIGN KEY (email) REFERENCES users (email) ON DELETE CASCADE,
        UNIQUE(email, record_date)
    );
    """)

    # 4. 特典管理テーブル（sなしの incentive に統一）
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incentive (
        incentive_id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        incentive_type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'locked',
        required_days INTEGER NOT NULL,
        expire_date TEXT,
        shop_name TEXT,
        FOREIGN KEY (email) REFERENCES users (email) ON DELETE CASCADE
    );
    """)

    # --- 🧪 テスト用の初期デモデータを注入 ---
    print("デモデータをデータベースに注入しています...")
    
    # テストユーザー（岩松君のバリデーションに完全一致する英数8文字）
    cursor.execute("INSERT INTO users (email, password, username) VALUES (?, ?, ?);", 
                   ("user@example.com", "pass1234", "千葉 太郎"))
    
    # ログイン管理（現在の最新である「12日」に設定）
    cursor.execute("INSERT INTO login_management (email, login_days, last_login_date, input_today_flag) VALUES (?, ?, ?, ?);",
                   ("user@example.com", 12, "2026-06-20", 0))

    # 特典データの初期状態（7日ジュース＝利用可、14日マッサージ＝ロック、温泉＝使用済）
    cursor.executemany("""
    INSERT INTO incentive (email, incentive_type, status, required_days, expire_date, shop_name)
    VALUES (?, ?, ?, ?, ?, ?);
    """, [
        ("user@example.com", "ジュース無料券", "available", 7, "残り7日", "◯◯温泉"),
        ("user@example.com", "マッサージチェア30分券", "locked", 14, "あと2日", "◯◯ドラッグストア"),
        ("user@example.com", "温泉入浴券", "used", 0, "使用済み", "◯◯温泉")
    ])

    conn.commit()
    conn.close()
    print("🎉 データベースの作成とデモデータの注入が完全に完了しました！('rehab_app.db' が作られました)")

if __name__ == "__main__":
    init_database()