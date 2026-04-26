let started = false;
function startRoom(skip=false){

  if(started) return;
  started = true;

  const saved = JSON.parse(localStorage.getItem("va_profile") || "null");

  let name, age, gender;

  if(skip){

    if(saved){
      // ✅ 既存ユーザー → 変更しない
      name = saved.name;
      age = saved.age;
      gender = saved.gender;

    } else {
      // ✅ 初回ユーザー → 匿名で開始
      name = "匿名";
      age = "";
      gender = "";
    }

  } else {
    // 通常入力
    name = document.getElementById("nickname").value.trim() || "匿名";
    age = document.getElementById("age").value || "";
    gender = document.getElementById("gender").value || "";
  }

  const profile = {name, age, gender};
  localStorage.setItem("va_profile", JSON.stringify(profile));

  // ① モーダルをソフトに閉じる
  const modal = document.getElementById("profile_modal");
  modal.classList.add("hide");

  setTimeout(() => {
    modal.style.display = "none";
  }, 300);

  // ② Welcome先に入れる
  document.getElementById("welcome").innerHTML =
    getJapanGreetingMessage(name);

  // ③ main表示（まだ透明）
  const main = document.getElementById("room_main");
  main.classList.remove("hidden");

  // ④ 遅延で背景クリア（ここがミソ）、その後にフェードイン
  setTimeout(() => {
    document.getElementById("blur_bg").classList.add("clear");
    main.classList.add("show");
  }, 300);

  loadRoomState();
}


async function loadRoomState(){

  const res = await fetch("/api/sessions");
  
  if(!res.ok){
    console.log("APIエラー");
    return;
  }
  
  const json = await res.json();

  const sessions = json.sessions || [];
  const area = document.getElementById("content_area");

  loadWeather();

  // ■ 分岐UI
  if(sessions.length === 0){

    area.innerHTML = `
      <div class="panel">
        <p>まだ記録がありません</p>
        <button onclick="goMini()">🎙 5秒で測定する</button>
      </div>
    `;

  } else {

    const latest = sessions[sessions.length - 1];

    area.innerHTML = `
      <div class="panel">
        <h2>今日の状態</h2>
        <p>Energy: ${latest.energy}</p>
        <p>Stress: ${latest.stress}</p>
        <p>Emotion: ${latest.emotion}</p>

        <button onclick="goHealth()">詳細を見る</button>
      </div>
    `;
  }
}


function goMini(){
  window.location.href = "https://mini.voiceaurahealth.com";
}

function goHealth(){
  window.location.href = "/health";
}

function openProfile(){
  started = false;  // ←これ追加 再入力がちゃんと動く
  
  const modal = document.getElementById("profile_modal");

  modal.classList.remove("hidden");
  modal.classList.remove("hide");   // ←これ追加

  modal.style.display = "flex";

  document.querySelector(".modal-box h2").innerText = "プロフィール変更";


  // 既存データをフォームに戻す
  const profile = JSON.parse(localStorage.getItem("va_profile") || "{}");

  document.getElementById("nickname").value = profile.name || "";
  document.getElementById("age").value = profile.age || "";
  document.getElementById("gender").value = profile.gender || "";
  
  // 🔥 ここ追加
  const skipBtn = document.querySelector(".skip");
  if(skipBtn){
    skipBtn.innerText = "変更しない";
  }
  
}

function goLab(){
  window.location.href = "/lab";
}

function goTeam(){
  window.location.href = "/team";
}

// 挨拶＋日本時間＋改行
function getJapanGreetingMessage(name){
  const now = new Date();

  const jp = new Date(
    now.toLocaleString("en-US", { timeZone: "Asia/Tokyo" })
  );

  const y = jp.getFullYear();
  const m = jp.getMonth() + 1;
  const d = jp.getDate();
  const h = jp.getHours();
  const min = String(jp.getMinutes()).padStart(2, "0");

  const weekdays = ["日", "月", "火", "水", "木", "金", "土"];
  const w = weekdays[jp.getDay()];

  let greet = "こんにちは";
  if(h < 11) greet = "おはようございます";
  else if(h >= 17) greet = "こんばんは";

  return `
    ${name}さん。<br>
    ${greet}。今日もお疲れさまでした。<br>
    <span class="today-text">
      今日は ${y}年${m}月${d}日（${w}）${h}:${min}
    </span>
  `;
}

// 無料天気APIへ問い合わせ
async function loadWeather(){
  if(!navigator.geolocation){
    return;
  }

  navigator.geolocation.getCurrentPosition(async pos => {
    const lat = pos.coords.latitude;
    const lon = pos.coords.longitude;

    const url =
      `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true&timezone=Asia%2FTokyo`;

    const res = await fetch(url);
    const data = await res.json();

    const weather = data.current_weather;
    if(!weather) return;

    document.getElementById("weather_box").innerHTML = `
      <div class="weather-box">
        🌤 外の気温：${weather.temperature}℃　
        風速：${weather.windspeed} km/h
      </div>
    `;
  });
}

// データのリセット
function resetAll(){

  const ok = confirm("⚠️ 本当に全データを削除しますか？\nこの操作は元に戻せません。");

  if(!ok) return;

  // プロフィール削除
  localStorage.removeItem("va_profile");

  // サーバーのセッション削除（API必要）
  fetch("/api/reset", { method: "POST" });

  // リロード
  location.reload();
}

function initRoom(){
  window.onload();
}

// 長押しリセット（誤操作防止）
let resetTimer = null;

function startResetPress(e){

  const btn = e.currentTarget;
  btn.classList.add("active");

  resetTimer = setTimeout(() => {

    const ok = confirm("⚠️ 全データ削除しますか？");

    if(!ok){
      btn.classList.remove("active");
      return;
    }

    localStorage.removeItem("va_profile");

    fetch("/api/reset", { method: "POST" });

    location.reload();

  }, 2000); // 2秒長押し

}

function cancelResetPress(e){
  const btn = e.currentTarget;
  btn.classList.remove("active");
  clearTimeout(resetTimer);
}

// roon設定　開
function openSettings(){
  const modal = document.getElementById("settings_modal");
  modal.classList.remove("hidden");
  modal.classList.remove("hide");
  modal.style.display = "flex";

  loadSettingsUI();
}

// roon設定　閉
function closeSettings(){
  const modal = document.getElementById("settings_modal");
  modal.classList.add("hide");

  setTimeout(() => {
    modal.style.display = "none";
  }, 300);
}

// roon設定　セーブ
function saveSettings(){

  const bg = document.querySelector('input[name="bg"]:checked')?.value;
  const music = document.querySelector('input[name="music"]:checked')?.value;
  const history = document.querySelector('input[name="history"]:checked')?.value;

  const settings = { bg, music, history };

  localStorage.setItem("va_settings", JSON.stringify(settings));

  applySettings(settings);

  closeSettings();
}

// roon設定　ロード
function loadSettingsUI(){

  const settings = JSON.parse(localStorage.getItem("va_settings") || "{}");

  if(settings.bg){
    const el = document.querySelector(`input[name="bg"][value="${settings.bg}"]`);
    if(el) el.checked = true;
  }

  if(settings.music){
    const el = document.querySelector(`input[name="music"][value="${settings.music}"]`);
    if(el) el.checked = true;
  }

  if(settings.history){
    const el = document.querySelector(`input[name="history"][value="${settings.history}"]`);
    if(el) el.checked = true;
  }
}

// roon設定　BGM音源
function applySettings(settings){

  // 一旦クラス全部消す（安全）
  document.body.classList.remove("bg1","bg2","bg3","bg4","bg5");

  if(settings.bg){
    document.body.classList.add(settings.bg);
  }

  // 音楽は後でOK

}


// 初回判定（コードの最後に）
window.onload = function(){

  const profile = localStorage.getItem("va_profile");

  if(profile){

    const p = JSON.parse(profile);

    // 名前安全化
    const name = (p.name || "匿名").trim() || "匿名";

    // モーダルをフェードアウト
    const modal = document.getElementById("profile_modal");
	
	// ←ここ追加（初期ちらつき防止）
//    modal.style.opacity = "1";
	
    modal.classList.add("hide");

    setTimeout(() => {
      modal.style.display = "none";
    }, 300);

    // Welcome
    document.getElementById("welcome").innerHTML =
      getJapanGreetingMessage(name);

    // main表示（まだ透明）
    const main = document.getElementById("room_main");
    main.classList.remove("hidden");

    // 世界を開く演出
    setTimeout(() => {
      document.getElementById("blur_bg").classList.add("clear");
      main.classList.add("show");
    }, 100);

    loadRoomState();
  }else {

		const modal = document.getElementById("profile_modal");

		// 🔥 モーダルを確実に表示
		modal.classList.remove("hidden");
		modal.classList.remove("hide");
		modal.style.display = "flex";

		// 🔥 フォーム初期化
		document.getElementById("nickname").value = "";
		document.getElementById("age").value = "";
		document.getElementById("gender").value = "";

		// 🔥 スキップ文言も戻す
		const skipBtn = document.querySelector(".skip");
		if(skipBtn){
			skipBtn.innerText = "スキップ（匿名で開始）";
		}

		// 🔥 背景演出
		setTimeout(() => {
			document.getElementById("blur_bg").classList.add("clear");
		}, 500);
	}
  
  const saved = localStorage.getItem("va_profile");
  const skipBtn = document.querySelector(".skip");

  if(skipBtn){
    if(saved){
      skipBtn.innerText = "変更しない";
    } else {
      skipBtn.innerText = "スキップ（匿名で開始）";
    }
	}

	const settings = JSON.parse(localStorage.getItem("va_settings") || "{}");
	applySettings(settings);

  
};