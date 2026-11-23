Three.js 0.149.0의 전역(Umd) 버전 파일을 이 폴더에 둡니다.

인터넷이 되는 PC에서 프로젝트 폴더 내에서:
  node download-three.cjs

성공 시 vendor/three.min.js 생성됩니다.
브라우저 로컬 실행 시 이 파일을 먼저 읽고, 없으면 CDN을 시도합니다.
두 경로 모두 실패해도 HTML5 Canvas 2D 렌더링으로 정상 표시됩니다.
