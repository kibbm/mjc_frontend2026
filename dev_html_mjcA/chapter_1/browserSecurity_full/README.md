# 브라우저는 나를 얼마나 알고 있을까?

웹 프로그래밍 / 웹보안 입문 수업용 HTML·CSS·JavaScript 프로젝트입니다.

## 파일

- `index.html` : 화면 구조
- `style.css` : 카드형 UI와 반응형 디자인
- `script.js` : Browser API와 버튼 이벤트

## 권장 실행 방법

1. VS Code에서 이 폴더를 엽니다.
2. Live Server 확장을 사용합니다.
3. `index.html`을 **Open with Live Server**로 실행합니다.
4. Chrome 또는 Edge에서 테스트합니다.

예: `http://127.0.0.1:5500/` 또는 `http://localhost:5500/`

## 실습 순서

1. 권한 없이 확인 가능한 브라우저/환경 정보
2. `enumerateDevices()`로 미디어 장치 확인
3. `getUserMedia()`로 마이크 권한 요청
4. Web Bluetooth가 지원되는 환경에서 사용자가 장치 선택
5. 현재 페이지가 확인한 값을 JSON으로 보기

## 중요

- 이 프로젝트는 수집 정보를 외부 서버로 전송하지 않습니다.
- 마이크 권한을 허용해도 스트림을 즉시 종료하며 녹음하지 않습니다.
- Web Bluetooth는 브라우저/OS에 따라 지원되지 않을 수 있습니다.
