function startRoom(skip=false){

  let name = document.getElementById("nickname").value || "匿名";
  let age = document.getElementById("age").value || "";
  let gender = document.getElementById("gender").value || "";

  if(skip){
    name = "匿名";
  }

  const profile = {name, age, gender};
  localStorage.setItem("va_profile", JSON.stringify(profile));

  document.getElementById("profile_modal").style.display = "none";

  // 背景をくっきり
  document.getElementById("blur_bg").classList.add("clear");

  // メイン表示
  document.getElementById("room_main").classList.remove("hidden");

  document.getElementById("welcome").innerText =
    `${name}さん、お疲れさまでした`;

  loadRoomState();
}


async function loadRoomState(){

  const res = await fetch("/api/sessions");
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
  document.getElementById("profile_modal").style.display = "flex";
}

// 初回判定
window.onload = function(){
  const profile = localStorage.getItem("va_profile");

  if(profile){
    const p = JSON.parse(profile);

    document.getElementById("profile_modal").style.display = "none";
    document.getElementById("blur_bg").classList.add("clear");
    document.getElementById("room_main").classList.remove("hidden");

    document.getElementById("welcome").innerText =
      `${p.name}さん、お疲れさまでした`;

    loadRoomState();
  }
};