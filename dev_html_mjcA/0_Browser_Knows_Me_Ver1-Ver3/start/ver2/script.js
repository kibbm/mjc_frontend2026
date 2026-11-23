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

// 이번 단계의 코드를 이 줄 아래에 붙여 넣으세요.
