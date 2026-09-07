// ======================================================
// 브라우저는 나를 얼마나 알고 있을까?
// HTML 요소 선택 → 버튼 이벤트 → Browser API 호출 순서로 읽어보세요.
// ======================================================

// 현재 페이지에서 확인한 값을 저장할 객체
const collectedData = {
  basic: {},
  mediaDevices: [],
  microphonePermission: "not requested",
  bluetooth: null
};


// ------------------------------------------------------
// STEP 1. 권한 없이 확인 가능한 기본 정보
// ------------------------------------------------------

const basicInfoBtn = document.querySelector("#basicInfoBtn");
const basicInfo = document.querySelector("#basicInfo");

basicInfoBtn.addEventListener("click", showBasicInfo);

function showBasicInfo() {
  const platform =
    navigator.userAgentData?.platform ||
    navigator.platform ||
    "확인 불가";

  const memory =
    navigator.deviceMemory !== undefined
      ? `${navigator.deviceMemory} GB 정도`
      : "브라우저가 제공하지 않음";

  const data = {
    platform: platform,
    logicalProcessors: navigator.hardwareConcurrency ?? "확인 불가",
    memory: memory,
    screen: `${screen.width} × ${screen.height}`,
    viewport: `${window.innerWidth} × ${window.innerHeight}`,
    language: navigator.language,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    touchPoints: navigator.maxTouchPoints,
    cookies: navigator.cookieEnabled ? "사용 가능" : "사용 불가",
    online: navigator.onLine ? "온라인" : "오프라인",
    secureContext: window.isSecureContext ? "보안 컨텍스트" : "일반 컨텍스트"
  };

  collectedData.basic = data;

  basicInfo.innerHTML = `
    ${makeCard("플랫폼", data.platform)}
    ${makeCard("논리 프로세서", data.logicalProcessors)}
    ${makeCard("메모리", data.memory)}
    ${makeCard("화면 해상도", data.screen)}
    ${makeCard("브라우저 창", data.viewport)}
    ${makeCard("언어", data.language)}
    ${makeCard("시간대", data.timezone)}
    ${makeCard("터치 포인트", data.touchPoints)}
    ${makeCard("쿠키", data.cookies)}
    ${makeCard("네트워크 상태", data.online)}
    ${makeCard("실행 환경", data.secureContext)}
  `;
}

function makeCard(title, value) {
  return `
    <article class="info-card">
      <h3>${escapeHtml(title)}</h3>
      <p>${escapeHtml(String(value))}</p>
    </article>
  `;
}


// ------------------------------------------------------
// STEP 2. 미디어 장치 목록 확인
// ------------------------------------------------------

const deviceBtn = document.querySelector("#deviceBtn");
const deviceList = document.querySelector("#deviceList");

deviceBtn.addEventListener("click", showMediaDevices);

async function showMediaDevices() {
  if (!navigator.mediaDevices?.enumerateDevices) {
    deviceList.textContent =
      "이 브라우저 또는 현재 실행 환경에서는 MediaDevices API를 사용할 수 없습니다.";
    return;
  }

  try {
    const devices = await navigator.mediaDevices.enumerateDevices();

    const simpleDevices = devices.map((device, index) => ({
      number: index + 1,
      kind: kindToKorean(device.kind),
      label: device.label || "이름 비공개"
    }));

    collectedData.mediaDevices = simpleDevices;

    if (simpleDevices.length === 0) {
      deviceList.textContent = "확인 가능한 미디어 장치가 없습니다.";
      return;
    }

    deviceList.innerHTML = simpleDevices
      .map(
        device => `
          <div class="device-item">
            ${device.number}. ${escapeHtml(device.kind)}
            : ${escapeHtml(device.label)}
          </div>
        `
      )
      .join("");

  } catch (error) {
    deviceList.textContent = `장치 확인 실패: ${error.message}`;
  }
}

function kindToKorean(kind) {
  if (kind === "audioinput") return "마이크/오디오 입력";
  if (kind === "audiooutput") return "스피커/오디오 출력";
  if (kind === "videoinput") return "카메라";
  return kind;
}


// ------------------------------------------------------
// STEP 3. 마이크 권한 요청
// ------------------------------------------------------

const micBtn = document.querySelector("#micBtn");
const permissionResult = document.querySelector("#permissionResult");

micBtn.addEventListener("click", requestMicrophone);

async function requestMicrophone() {
  if (!navigator.mediaDevices?.getUserMedia) {
    permissionResult.textContent =
      "현재 환경에서는 getUserMedia()를 사용할 수 없습니다. localhost 또는 HTTPS에서 실행해 보세요.";
    return;
  }

  try {
    // 사용자에게 마이크 권한을 요청한다.
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: true
    });

    collectedData.microphonePermission = "granted";

    permissionResult.textContent =
      "마이크 권한이 허용되었습니다. 오디오 스트림은 즉시 종료했습니다.";

    // 실습에서 실제 녹음은 하지 않으므로 곧바로 종료한다.
    stream.getTracks().forEach(track => track.stop());

    // 권한 허용 후 장치 이름이 더 보이는지 다시 확인한다.
    await showMediaDevices();

  } catch (error) {
    collectedData.microphonePermission = "denied or failed";

    permissionResult.textContent =
      `마이크 권한을 얻지 못했습니다: ${error.name}`;
  }
}


// ------------------------------------------------------
// STEP 4. Web Bluetooth
// ------------------------------------------------------

const bluetoothBtn = document.querySelector("#bluetoothBtn");
const bluetoothResult = document.querySelector("#bluetoothResult");

bluetoothBtn.addEventListener("click", selectBluetoothDevice);

async function selectBluetoothDevice() {
  if (!navigator.bluetooth) {
    bluetoothResult.textContent =
      "이 브라우저에서는 Web Bluetooth를 지원하지 않거나 현재 환경에서 사용할 수 없습니다.";
    return;
  }

  try {
    // 반드시 사용자가 브라우저의 장치 선택창에서 장치를 선택한다.
    const device = await navigator.bluetooth.requestDevice({
      acceptAllDevices: true
    });

    const deviceName = device.name || "이름 없는 Bluetooth 장치";

    collectedData.bluetooth = {
      selectedByUser: true,
      name: deviceName
    };

    bluetoothResult.textContent =
      `사용자가 선택한 장치: ${deviceName}`;

  } catch (error) {
    if (error.name === "NotFoundError") {
      bluetoothResult.textContent =
        "장치를 선택하지 않았거나 선택 창을 취소했습니다.";
    } else {
      bluetoothResult.textContent =
        `Bluetooth 사용 실패: ${error.name}`;
    }
  }
}


// ------------------------------------------------------
// STEP 5. 지금까지 수집한 정보를 JSON으로 확인
// ------------------------------------------------------

const jsonBtn = document.querySelector("#jsonBtn");
const jsonResult = document.querySelector("#jsonResult");

jsonBtn.addEventListener("click", showCollectedJson);

function showCollectedJson() {
  jsonResult.textContent =
    JSON.stringify(collectedData, null, 2);
}


// ------------------------------------------------------
// 화면에 문자열을 넣을 때 HTML 코드로 해석되지 않도록 처리
// ------------------------------------------------------

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
