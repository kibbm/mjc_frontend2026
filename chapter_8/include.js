// defer로 실행하므로 HTML의 data-include 요소를 읽을 수 있습니다.
document.querySelectorAll("[data-include]").forEach(async (element) => {
    const file = element.dataset.include;

    try {
        const response = await fetch(file);
        if (!response.ok) {
            throw new Error(`${file}: HTTP ${response.status}`);
        }

        // 이 프로젝트에서 작성한 공통 HTML 조각을 현재 페이지에 삽입합니다.
        element.innerHTML = await response.text();
    } catch (error) {
        element.textContent = "공통 메뉴를 불러오지 못했습니다.";
        console.error("HTML include 실패:", error);
    }
});
