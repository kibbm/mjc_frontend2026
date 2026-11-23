// 버튼을 누른 시점의 값을 읽습니다.
const select = selector => document.querySelector(selector);
const observed = {};

function showBasicInfo() {
  observed.basic = {
    언어: navigator.language,
    시간대: Intl.DateTimeFormat().resolvedOptions().timeZone,
    화면: screen.width + " × " + screen.height,
    창: window.innerWidth + " × " + window.innerHeight
  };
  select("#basicInfo").textContent = Object.entries(observed.basic)
    .map(([name, value]) => name + " · " + value)
    .join("\n");
}

select("#basicInfoBtn").addEventListener("click", showBasicInfo);

// 목록 조회와 마이크 사용 요청은 서로 다른 동작입니다.
async function showDevices() {
  const output = select("#deviceList");
  if (!navigator.mediaDevices?.enumerateDevices) {
    observed.devices = null;
    output.textContent = "목록 조회를 지원하지 않습니다. 실행 주소를 확인하세요.";
    return;
  }
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    observed.devices = devices.map(device => ({
      종류: device.kind,
      이름: device.label || "이름 비공개"
    }));
    output.textContent = observed.devices
      .map(device => device.종류 + " · " + device.이름)
      .join("\n") || "표시 가능한 장치가 없습니다.";
  } catch (error) {
    observed.devices = null;
    output.textContent = "목록 확인 실패 · " + error.name;
  }
}

async function checkMic() {
  const output = select("#permissionResult");
  if (!navigator.mediaDevices?.getUserMedia) {
    observed.micResult = "사용 불가";
  } else {
    try {
      output.textContent = "마이크 요청 결과를 기다리는 중입니다.";
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      observed.micResult = "허용됨 · 스트림 종료";
    } catch (error) {
      observed.micResult = "요청 실패 · " + error.name;
    }
  }
  output.textContent = observed.micResult;
  await showDevices();
}

select("#deviceBtn").addEventListener("click", showDevices);
select("#micBtn").addEventListener("click", checkMic);

// 사용자가 고른 장치 이름만 표시합니다.
async function chooseDevice() {
  if (!navigator.bluetooth?.requestDevice) {
    observed.bluetooth = "이 환경에서 사용 불가";
  } else {
    try {
      const device = await navigator.bluetooth.requestDevice({
        acceptAllDevices: true
      });
      observed.bluetooth = device.name || "이름 없는 장치 선택";
    } catch (error) {
      observed.bluetooth = error.name === "NotFoundError"
        ? "선택된 장치 없음"
        : "선택 실패 · " + error.name;
    }
  }
  select("#bluetoothResult").textContent = observed.bluetooth;
}

function showJson() {
  select("#jsonResult").textContent = JSON.stringify(observed, null, 2);
}

select("#bluetoothBtn").addEventListener("click", chooseDevice);
select("#jsonBtn").addEventListener("click", showJson);
