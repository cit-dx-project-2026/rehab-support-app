// ==========================================
// 1. 【ユーザーテスト用】外注委託（想定）のコアシステムダミーデータ
// ==========================================
const coreSystemData = {
    loginDays: 8,
    aiAdvice: "素晴らしい継続です！この調子で健康管理を続けましょう。",
    nextReward: "マッサージチェア30分券",
    announcements: [
        { date: "2026/05/10", title: "新緑のリハビリウォーキング大会開催のお知らせ" },
        { date: "2026/05/08", title: "【重要】夏季休診期間（8/11〜8/15）について" }
    ]
};

// ==========================================
// 2. 【ご友人発案】ログイン情報を自動チェックして守る共通関数
// ==========================================
function checkAuth() {
    // ブラウザの一時保存ポケット（localStorage）からユーザーIDを取り出す
    const userId = localStorage.getItem('login_user_id');

    // もしポケットに何も入っていなければ（未ログインの不正アクセス）
    if (!userId) {
        alert("ログインが必要です。ログイン画面に戻ります。");
        window.location.href = "login.html"; // ログイン画面へ強制送還
        return null;
    }

    // ログインしていれば、そのユーザーIDを返す
    return userId;
}

// ログイン成功時にポケットにIDをしまう関数（岩松さんの画面で呼び出す）
function saveLoginInfo(userId) {
    localStorage.setItem('login_user_id', userId);
}

// ログアウト時にポケットを空にする関数（上野さんの画面で呼び出す）
function logout() {
    localStorage.removeItem('login_user_id');
    window.location.href = "login.html";
}

// ==========================================
// 3. 【デモ用】ホーム画面にダミーデータを反映させる関数
// ==========================================
function loadHomeData() {
    const userId = checkAuth(); // まずログインチェック
    if (!userId) return;

    // 各HTML要素にデータを流し込む（要素が存在する場合のみ）
    if(document.getElementById('display-login-days')) {
        document.getElementById('display-login-days').innerText = coreSystemData.loginDays;
    }
    if(document.getElementById('display-ai-advice')) {
        document.getElementById('display-ai-advice').innerText = coreSystemData.aiAdvice;
    }
    if(document.getElementById('display-next-reward')) {
        document.getElementById('display-next-reward').innerText = coreSystemData.nextReward;
    }
}
// ==========================================
// 4. 【鈴木追加】ログイン日数カウントアップ＆取得ロジック
// ==========================================
function incrementLoginDays() {
    // ローカルストレージから現在の日数を取得（なければ初期値の8日をベースにする）
    let currentDays = parseInt(localStorage.getItem('login_days')) || 8;
    
    // 日数を1日プラスする
    currentDays += 1;
    
    // ストレージのデータを最新の状態に更新
    localStorage.setItem('login_days', currentDays);
}

function getLoginDays() {
    // 保存されている最新の日数を返す（まだなければ初期値8）
    return parseInt(localStorage.getItem('login_days')) || 8;
}

// 💡 鈴木作成：サーバーからユーザー個別の最新ログイン日数を取得して画面に反映する関数
async function refreshLoginDays() {
    const userId = localStorage.getItem("user_id"); // ログイン時に保存したemail
    const apiKey = "rehab-support-app-2026-key";

    if (!userId) {
        console.error("ユーザーIDがローカルストレージにありません。");
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:5000/api/v1/login-status?user_id=${encodeURIComponent(userId)}`, {
            method: "GET",
            headers: {
                "X-API-KEY": apiKey,
                "Content-Type": "application/json"
            }
        });

        if (response.ok) {
            const data = await response.json();
            console.log("DBから取得したログイン日数:", data.login_days);
            
            // ➔ ここで、中間君のホーム画面や、鈴木さんの特典画面の「日数表示テキスト」や「ゲージ」に数字をハメ込みます！
            // 例：
            const daysElement = document.getElementById("login-days-display");
            if (daysElement) {
                daysElement.textContent = data.login_days;
            }
            
            // 他の画面の既存ロジック用にLocalStorageのキャッシュも最新にしておく
            localStorage.setItem("loginDays", data.login_days);
            localStorage.setItem("inputTodayFlag", data.input_today_flag);
            
        } else {
            console.error("ログインステータスの取得に失敗しました。");
        }
    } catch (error) {
        console.error("通信エラー:", error);
    }
}