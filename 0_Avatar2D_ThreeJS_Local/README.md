# Three.js 기반 2D 아바타 메이커 — 실행 및 수정 안내

## 이전 아바타가 보이지 않았던 이유
기존 코드에서 `three@0.160.0/build/three.min.js` 및 `examples/js/controls/OrbitControls.js`를 사용했습니다. 해당 버전에서는 구형 전역 스크립트 배포 경로가 제거되었으므로 `THREE`가 정의되지 않아 실행이 중단될 수 있습니다.

## 이번 수정의 핵심
- **HTML5 Canvas 2D를 먼저 표시**하므로 Three.js 로딩 실패에도 아바타 얼굴과 몸이 보입니다.
- 사용 가능한 경우 **Three.js OrthographicCamera + CanvasTexture + MeshBasicMaterial**을 사용해 2D 아바타를 정사영 화면에 표시합니다.
- 3D 전신 모델을 그리는 것이 아닌, 레이어를 겹쳐 만든 정면 2D 캐릭터입니다.
- 별도의 캐릭터 이미지, 외부 모델(GLB/GLTF), NPM 패키지가 필요 없습니다.
- 브라우저 화면 상단에 현재 사용 중인 엔진이 표시됩니다.

## 실행 ①: 인터넷 없이 바로 실행 (HTML5 Canvas 2D)
- 단일 파일 `ThreeJS_2D_아바타_메이커_수정.html`을 더블클릭합니다.
- 브라우저가 열리면 즉시 아바타와 꾸미기 메뉴가 표시됩니다.
- Three.js를 내려받지 못하면 상단에 **HTML5 2D (오프라인)**이라고 표시됩니다.
- 이 상태에서도 모든 꾸미기·랜덤·저장·PNG 기능은 작동합니다.

## 실행 ②: Three.js 사용, 로컬에서도 오프라인 사용
인터넷 연결이 되는 Windows/macOS PC에서 한 번만 다음을 실행합니다.

```bash
cd Avatar2D_ThreeJS_Local
node download-three.cjs
```

`vendor/three.min.js`가 저장됩니다. 이후 `index.html`을 브라우저로 직접 열면 **Three.js 정사영 2D**로 렌더링합니다. `node`는 Three.js 파일을 다운로드할 때만 필요하며, 실행 자체에 Node.js는 필요하지 않습니다.

인터넷 연결이 있고 vendor 파일이 없어도 브라우저는 동일한 버전의 Three.js를 CDN에서 불러오도록 시도합니다. 성공하면 모드를 자동으로 전환합니다.

## VS Code 실행
1. ZIP을 압축 해제하고 폴더를 VS Code에서 엽니다.
2. `index.html`을 `Live Server`로 실행하거나 더블클릭해도 됩니다.
3. 오프라인 Three.js가 필요하면 미리 `node download-three.cjs`를 실행합니다.

## 기능
- 6개 아바타 프리셋, 체형 4종, 포즈 3종
- 얼굴형 5종, 눈 5종, 입 4종, 눈썹 3종, 주근깨
- 헤어 7종, 상의 5종, 하의 4종, 신발 3종
- 안경 3종, 모자 4종, 귀걸이 2종, 목걸이 2종, 가방 2종 및 '없음'
- 색상 선택, 실시간 갱신, 확대/축소
- 로컬 저장/불러오기, JSON 저장/불러오기, 투명 PNG 다운로드

## 파일 구조
```
Avatar2D_ThreeJS_Local/
  index.html
  css/style.css
  js/app.js
  vendor/README.txt
  download-three.cjs
  README.md
```

## 수정 위치
- `js/app.js`의 `templates`: 기본 아바타 프리셋
- `drawFace`, `drawHairFront`, `hairBack`: 얼굴 및 헤어 디자인
- `legs`, `arm`, `torso`, `bagAndNecklace`: 의상·체형·장식
- `activateThree`: Three.js 정사영 화면
- `css/style.css`: 웹 인터페이스 디자인

## 제한사항
- 카툰형 2D 벡터 캐릭터입니다. 실사 인물 모델이나 3D 회전 모델은 아닙니다.
- 저장되는 JSON은 아바타 설정 데이터이며 메시/GLB 파일이 아닙니다.
- `file://` 환경에서 `localStorage`가 제한되는 브라우저는 JSON으로 내보내기를 사용하세요.
