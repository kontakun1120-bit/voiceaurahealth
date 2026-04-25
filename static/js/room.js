let started = false;

function startRoom(skip=false){

  if(started) return;
  started = true;

  let name = document.getElementById("nickname").value.trim() || "匿名";
  let age = document.getElementById("age").value || "";
  let gender = document.getElementById("gender").value || "";

  if(skip){
    name = "匿名";
  }

  const profile = {name, age, gender};
  localStorage.setItem("va_profile", JSON.stringify(profile));

  // ① モーダル閉じる
  document.getElementById("profile_modal").style.display = "none";

  // ② Welcome先に入れる
  document.getElementById("welcome").innerText =
    `${name}さん、お疲れさまでした`;

  // ③ main表示（まだ透明）
  document.getElementById("room_main").classList.remove("hidden");

  // ④ 遅延で背景クリア（ここがミソ）
  setTimeout(() => {
    document.getElementById("blur_bg").classList.add("clear");

  // ① モーダル フェードアウト
  document.getElementById("profile_modal").classList.add("hide");

  // ⑤ その後にフェードイン
    document.getElementById("room_main").classList.add("show");

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
  document.querySelector(".modal-box h2").innerText = "プロフィール変更";
  document.getElementById("profile_modal").classList.remove("hide");
  document.getElementById("profile_modal").style.display = "flex";

  // 既存データをフォームに戻す
  const profile = JSON.parse(localStorage.getItem("va_profile") || "{}");

  document.getElementById("nickname").value = profile.name || "";
  document.getElementById("age").value = profile.age || "";
  document.getElementById("gender").value = profile.gender || "";
}

// 初回判定
window.onload = function(){

  const profile = localStorage.getItem("va_profile");

  if(profile){

    const p = JSON.parse(profile);

    // 名前安全化
    const name = (p.name || "匿名").trim() || "匿名";

    // モーダルをフェードアウト
    const modal = document.getElementById("profile_modal");
    modal.classList.add("hide");

    setTimeout(() => {
      modal.style.display = "none";
    }, 300);

    // Welcome
    document.getElementById("welcome").innerText =
      `${name}さん、お疲れさまでした`;

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

    // 🔥 初回演出（ここ）
    setTimeout(() => {
      document.getElementById("blur_bg").classList.add("clear");
    }, 500);

  }
  
};