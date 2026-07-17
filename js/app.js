// ==========================================
// 1. 【ユーザーテスト用】外注委託（想定）のコアシステムダミーデータ
// ==========================================
const coreSystemData = {
    loginDays: 14,
    aiAdvice: "素晴らしい継続です！この調子で健康管理を続けましょう。",
    nextReward: "温泉入浴券",
    announcements: [
        { date: "2026/05/10", title: "新緑のリハビリウォーキング大会開催のお知らせ" },
        { date: "2026/05/08", title: "【重要】夏季休診期間（8/11〜8/15）について" }
    ]
};

// ==========================================
// 2. 【共通処理】ログイン情報を自動チェックして守る共通関数
// ==========================================
function checkAuth() {
    const userId = localStorage.getItem('login_user_id');
    if (!userId) {
        alert("ログインが必要です。ログイン画面に戻ります。");
        window.location.href = "login.html";
        return null;
    }
    return userId;
}

function saveLoginInfo(userId) {
    localStorage.setItem('login_user_id', userId);
}

function logout() {
    localStorage.removeItem('login_user_id');
    window.location.href = "login.html";
}

// ==========================================
// 3. 【本物同期】ホーム画面および各画面に最新のDBデータを反映させる関数
// ==========================================
async function refreshLoginDays() {
    // 💡キー名を岩松君の login_user_id に完全統一
    const userId = localStorage.getItem("login_user_id") || "user@example.com"; 
    const apiKey = "rehab-support-app-2026-key";

    try {
        const response = await fetch(`/api/v1/login-status?user_id=${encodeURIComponent(userId)}`, {
            method: "GET",
            headers: {
                "X-API-KEY": apiKey,
                "Content-Type": "application/json"
            }
        });

        if (response.ok) {
            const data = await response.json();
            console.log("[DB SYNC] 最新のログイン日数:", data.login_days);
            
            // 各画面の要素があればピンポイントで本物の値をハメ込む
            const daysElement = document.getElementById("display-login-days");
            if (daysElement) {
                daysElement.innerHTML = data.login_days + '<span>日</span>';
            }

            const adviceElement = document.getElementById("display-ai-advice");
            if (adviceElement) {
                if (data.login_days >= 14) {
                    adviceElement.textContent = "2週間突破！立派な習慣が身についています";
                } else if (data.login_days >= 7) {
                    adviceElement.textContent = "素晴らしい継続です！次の特典まであと一歩！";
                } else {
                    adviceElement.textContent = "毎日の記録が健康への第一歩です。この調子で続けましょう！";
                }
            }
            
            // 互換性のためにLocalStorageも最新化
            localStorage.setItem("loginDays", data.login_days);
            localStorage.setItem("inputTodayFlag", data.input_today_flag ? "true" : "false");
            return data;
        }
    } catch (error) {
        console.error("通信エラー:", error);
    }
    return null;
}

// 💡古いダミーロード関数を、新設した本物通信関数へ安全にバイパス（橋渡し）する設定
function loadHomeData() {
    refreshLoginDays();
}

function getLoginDays() {
    return parseInt(localStorage.getItem('loginDays')) || 14;
}