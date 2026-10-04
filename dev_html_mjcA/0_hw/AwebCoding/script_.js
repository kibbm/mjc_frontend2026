const message = document.querySelector("#message");
const checkButton = document.querySelector("#checkButton");
const result = document.querySelector("#result");

/* 의심 표현 목록 */
const dangerWords = [
    "긴급",     "즉시",     "지금 바로",     "계정 정지",     "인증",
    "비밀번호",     "인증번호",     "송금",     "입금",     "결제" ];

function checkMessage() {
    const text = message.value.trim();
    /* 입력 확인 */
    if (text === "") {
        result.className = "result-box warning";
        result.textContent =
            "확인할 메시지를 먼저 입력해 주세요.";
        return;    }

    let score = 0;
    let foundWords = [];

    /* 위험 단어 확인 */
    for (let i = 0; i < dangerWords.length; i++) {
        if (text.includes(dangerWords[i])) {
            score = score + 1;
            foundWords.push(dangerWords[i]);
        }
    }

    /* 링크처럼 보이는 문자열 확인 */
    if (text.includes("http://") || text.includes("https://") || text.includes("www.") ) {
        score = score + 1;
        foundWords.push("링크");
    }

    /* 결과 판정 */
    if (score >= 3) {
        result.className = "result-box danger";
        result.textContent =
            "위험 신호가 여러 개 발견되었습니다. " +
            "링크를 클릭하거나 개인정보를 입력하지 말고 " +
            "공식 사이트에서 다시 확인하세요. " +
            "확인된 요소: " + foundWords.join(", ");
    } else if (score >= 1) {
        result.className = "result-box warning";
        result.textContent =
            "주의가 필요한 표현이 발견되었습니다. " +
            "발신자와 링크 주소를 다시 확인하세요. " +
            "확인된 요소: " + foundWords.join(", ");
    } else {
        result.className = "result-box safe";
        result.textContent =
            "현재 설정한 기준에서는 뚜렷한 위험 표현을 찾지 못했습니다. " +
            "하지만 실제 피싱 여부를 보장하는 결과는 아닙니다.";
    }
}
checkButton.addEventListener("click", checkMessage);

/*
6. script.js : 여기가 과제에서 가장 중요합니다.
AI나 머신러닝으로 피싱을 판별하는 것이 아닙니다.

학생이 Ch9에서 배운:
- 변수
- 배열
- 반복문
- 조건문
- 함수
와 Ch10의:
- querySelector
- addEventListener
- textContent
- className
정도만 이용합니다.


*/