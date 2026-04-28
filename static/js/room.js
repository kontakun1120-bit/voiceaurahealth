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
	if(modal){
		modal.classList.add("hide");
		setTimeout(()=>{
			modal.style.display = "none";
		},300);
	}

  setTimeout(() => {
    modal.style.display = "none";
  }, 300);

	// ② Welcome先に入れる
	const msg = getJapanGreetingMessage(name);
	const lines = msg.split("<br>");

	document.getElementById("welcome-name").innerHTML = lines[0];
	document.getElementById("welcome-sub").innerHTML = lines.slice(1).join("<br>");

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

  let json;

  try{
    const res = await fetch("/api/sessions");

    if(!res.ok) throw new Error("API error");

    json = await res.json();

  }catch(e){
    console.log("通信エラー", e);
    return;
  }

  const sessions = json.sessions || [];
  const area = document.getElementById("content_area");

  loadWeather();

  if(sessions.length === 0){
    area.innerHTML = `
      <div class="panel">
        <p>まだ記録がありません</p>
        <button onclick="goMini()">🎙 5秒で測定する</button>
      </div>
    `;
  }else{
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

  const title = document.querySelector(".modal-box h2");
	if(title){
		title.innerText = "プロフィール変更";
	}


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

  const jp = new Date();

  // ←ここ重要
  const options = { timeZone: "Asia/Tokyo", hour12: false };

  const parts = new Intl.DateTimeFormat("ja-JP", {
    ...options,
    year: "numeric",
    month: "numeric",
    day: "numeric",
    weekday: "short",
    hour: "numeric",
    minute: "2-digit"
  }).formatToParts(jp);

  const get = (type) => parts.find(p => p.type === type)?.value;

  const y = get("year");
  const m = get("month");
  const d = get("day");
  const h = parseInt(get("hour"));
  const min = get("minute");
  const w = get("weekday");

	if(h >= 0 && h < 5){
		greet = "こんばんは";
	}
	else if(h >= 5 && h < 11){
		greet = "おはようございます";
	}
	else if(h >= 11 && h < 17){
		greet = "こんにちは";
	}
	else{
		greet = "こんばんは";
	}

  return `
    ${name}さん。<br>
    ${greet}。<br>
    今日もお疲れさまでした。<br>
    <span class="today-text">
      現在は ${y}年${m}月${d}日（${w}）${h}:${min}
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

// room設定　開
let bgEventSet = false;

function openSettings(){
  const modal = document.getElementById("settings_modal");
  modal.classList.remove("hidden");
  modal.classList.remove("hide");
  modal.style.display = "flex";

  loadSettingsUI();
	
  // タブ初期化
  switchTab("bg");
	
  // 🔥 ここ追加（確実に効く）
	if(!bgEventSet){

		document.querySelectorAll('input[name="bg"]').forEach(radio => {

			radio.onchange = () => {

				const s = JSON.parse(localStorage.getItem("va_settings") || "{}");

				// 変更チェック（無駄処理防止）
				if(s.bg === radio.value) return;

				s.bg = radio.value;

				localStorage.setItem("va_settings", JSON.stringify(s));

				applySettings(s);
			};

		});

		bgEventSet = true;
	}
}


// room設定　閉
function closeSettings(){
  const modal = document.getElementById("settings_modal");
  modal.classList.add("hide");
}

// room設定　セーブ
function saveSettings(){

  const bg = document.querySelector('input[name="bg"]:checked')?.value;
  const music = document.querySelector('input[name="music"]:checked')?.value;
  const history = document.querySelector('input[name="history"]:checked')?.value;
	const time = document.querySelector('input[name="time"]:checked')?.value;

	const settings = { bg, music, history, time };

  localStorage.setItem("va_settings", JSON.stringify(settings));

  applySettings(settings);

  closeSettings();
}

// room設定　ロード
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

	if(settings.time){
		const el = document.querySelector(`input[name="time"][value="${settings.time}"]`);
		if(el) el.checked = true;
	}
}

// room中の設定タブ
function switchTab(type, e){

  // タブボタン
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  if(e) e.target.classList.add("active");

  // コンテンツ
  document.querySelectorAll(".tab-content").forEach(c => {
    c.classList.remove("active");
    c.classList.add("hidden");
  });

  const target = document.getElementById("tab-" + type);

  target.classList.remove("hidden");

  setTimeout(() => {
    target.classList.add("active");
  }, 10);
}

// 設定の開閉
function toggleSection(el){
  const parent = el.parentElement;
  parent.classList.toggle("open");

  // ▼切替
  if(parent.classList.contains("open")){
    el.innerText = el.innerText.replace("▶","▼");
  }else{
    el.innerText = el.innerText.replace("▼","▶");
  }
}

// roomの背景・サウンド連動
let currentTimeMode = null;

function applySettings(settings){

  // 背景
  document.body.classList.remove("bg1","bg2","bg3","bg4","bg5");

  if(settings.bg){
    document.body.classList.add(settings.bg);
  }

  // 🔥 時間フィルター
  applyTimeFilter(settings.time);

	// 時間決定
  let mode = settings.time || "auto";

  if(mode === "auto"){
    const h = new Date().getHours();
    if(h < 10) mode = "morning";
    else if(h < 17) mode = "day";
    else mode = "night";
  }

	// フェード適用
  if(mode !== currentTimeMode){
    fadeToTime(mode);
    currentTimeMode = mode;
  }

  // 🔊 音楽制御
	const audio = document.getElementById("bgm");

	if(audio){
		if(settings.music === "on"){
			audio.src = "/static/sound/forest.mp3";
			audio.volume = settings.volume || 0.3;
			audio.play().catch(()=>{});
		}else{
			audio.pause();
		}
	}
}

// roomの背景の照明を変化
function applyTimeFilter(mode){

  document.body.classList.remove("time-morning","time-day","time-night");

  if(!mode || mode === "auto"){
    const h = new Date().getHours();
    if(h < 10) mode = "morning";
    else if(h < 17) mode = "day";
    else mode = "night";
  }

  if(mode === "morning") document.body.classList.add("time-morning");
  if(mode === "day") document.body.classList.add("time-day");
  if(mode === "night") document.body.classList.add("time-night");
}

// roomの背景の照明を変化 （フェード対応）
function getTargetColor(mode){
  if(mode === "morning") return {r:255,g:220,b:150,a:0.15};
  if(mode === "day")     return {r:255,g:255,b:255,a:0.05};
  return {r:0,g:0,b:50,a:0.4}; // night
}

let fadeTimer = null;
function fadeToTime(mode, duration=30000){

  if(fadeTimer){
    clearInterval(fadeTimer);
  }

  const target = getTargetColor(mode);

  // 現在値
  const style = getComputedStyle(document.body);
  let cr = parseFloat(style.getPropertyValue("--t-r")) || 0;
  let cg = parseFloat(style.getPropertyValue("--t-g")) || 0;
  let cb = parseFloat(style.getPropertyValue("--t-b")) || 50;
  let ca = parseFloat(style.getPropertyValue("--t-a")) || 0.4;

  const step = 30; // ms
  const steps = duration / step;

  let i = 0;

  fadeTimer = setInterval(()=>{
    i++;

    const t = i / steps;

    document.body.style.setProperty("--t-r", cr + (target.r - cr) * t);
    document.body.style.setProperty("--t-g", cg + (target.g - cg) * t);
    document.body.style.setProperty("--t-b", cb + (target.b - cb) * t);
    document.body.style.setProperty("--t-a", ca + (target.a - ca) * t);

    if(i >= steps){
      clearInterval(fadeTimer);
      fadeTimer = null;
    }

  }, step);
}

/////////// 初回判定（コードの最後に)
// プロフィール
function initProfile(){

  const profile = localStorage.getItem("va_profile");

  if(profile){
    showRoom(JSON.parse(profile));
  }else{
    showModal();
  }
}

// プロフィールの子プロセス1/2
function showRoom(profile){

  const name = (profile.name || "匿名").trim() || "匿名";

  // モーダル閉じる
  const modal = document.getElementById("profile_modal");
  modal.classList.add("hide");

  setTimeout(()=>{
    modal.style.display = "none";
  },300);

  // welcome
  const msg = getJapanGreetingMessage(name);
  const lines = msg.split("<br>");

  document.getElementById("welcome-name").innerHTML = lines[0];
  document.getElementById("welcome-sub").innerHTML = lines.slice(1).join("<br>");

  // 表示
  const main = document.getElementById("room_main");
  main.classList.remove("hidden");

  setTimeout(()=>{
    document.getElementById("blur_bg").classList.add("clear");
    main.classList.add("show");
  },100);

  loadRoomState();
}

// プロフィールの子プロセス2/2
function showModal(){

  const modal = document.getElementById("profile_modal");

  modal.classList.remove("hidden");
  modal.classList.remove("hide");
  modal.style.display = "flex";

  document.getElementById("nickname").value = "";
  document.getElementById("age").value = "";
  document.getElementById("gender").value = "";

  const skipBtn = document.querySelector(".skip");
  if(skipBtn){
    skipBtn.innerText = "スキップ（匿名で開始）";
  }

  setTimeout(()=>{
    document.getElementById("blur_bg").classList.add("clear");
  },500);
}

// UI
function initUI(){
  document.getElementById("blur_bg").classList.add("clear");
}

// 設定
function initSettings(){

  const settings = JSON.parse(localStorage.getItem("va_settings") || "{}");

  applySettings(settings);

  // 音量初期化
  const audio = document.getElementById("bgm");
  const vol = document.getElementById("volume");

  const savedVol = settings.volume || 0.3;

  if(audio) audio.volume = savedVol;
  if(vol) vol.value = savedVol;
}

// イベント
function initEvents(){

	const vol = document.getElementById("volume");

	if(vol){

		vol.oninput = () => {   // ← addEventListener → oninput

			const audio = document.getElementById("bgm");

			if(audio){
				audio.volume = vol.value;
			}

			const s = JSON.parse(localStorage.getItem("va_settings") || "{}");
			s.volume = vol.value;
			localStorage.setItem("va_settings", JSON.stringify(s));
		};
	}
}

window.onload = function(){

  initProfile();   // ←プロフィール判定
  initUI();        // ←背景演出
  initSettings();  // ←設定適用
  initEvents();    // ←イベント登録

};