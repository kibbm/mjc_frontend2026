# 검증 기록

- JavaScript 구문 검사: `node --check js/app.js` 통과.
- 스키아 캔버스 기반 벡터 렌더링 검증: 기본형, 긴 머리+스커트, 재킷+반바지+한손 인사, 올림머리+양손 올리기 네 가지 조합에서 모두 유효한 불투명 픽셀과 전신 바운딩 박스 확인.
- mock DOM 이벤트 검증: 프리셋 6개 생성, 상의 색상 실시간 갱신, localStorage 저장→랜덤 생성→불러오기 복원 통과.
- 실제 Chrome 실행 및 WebGL/Three.js 전환: 이 제작 환경의 Chromium 관리 정책이 로컬 파일과 HTTP 접속을 차단하여 미검증. 반드시 사용자 PC의 Chrome/Edge/Safari에서 확인할 것.
- `vendor/three.min.js`: 현재 ZIP에 라이브러리 바이너리는 포함되지 않음. `node download-three.cjs`를 한 번 실행하면 다운로드되어 오프라인 Three.js가 가능하다. 다운로드 전에도 Canvas 2D가 정상 표시된다.
