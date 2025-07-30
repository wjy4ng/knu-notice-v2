const CATEGORIES = [
  {
    name: '공지사항',
    boards: [
      {
        name: '학생소식',
        url: 'https://www.kongju.ac.kr/KNU/16909/subview.do',
      },
      {
        name: '행정소식',
        url: 'https://www.kongju.ac.kr/KNU/16910/subview.do',
      },
      {
        name: '행사안내',
        url: 'https://www.kongju.ac.kr/KNU/16911/subview.do',
      },
      {
        name: '채용소식',
        url: 'https://www.kongju.ac.kr/KNU/16917/subview.do',
      },
    ],
  },
  {
    name: '곰나루광장',
    boards: [
      {
        name: '열린광장',
        url: 'https://www.kongju.ac.kr/KNU/16921/subview.do',
      },
      {
        name: '신문방송사',
        url: 'https://www.kongju.ac.kr/KNU/16922/subview.do',
      },
      {
        name: '스터디/모임',
        url: 'https://www.kongju.ac.kr/KNU/16923/subview.do',
      },
      {
        name: '분실물센터',
        url: 'https://www.kongju.ac.kr/KNU/16924/subview.do',
      },
      {
        name: '사고팔고',
        url: 'https://www.kongju.ac.kr/KNU/16925/subview.do',
      },
      {
        name: '자취하숙',
        url: 'https://www.kongju.ac.kr/KNU/16926/subview.do',
      },
      {
        name: '아르바이트',
        url: 'https://www.kongju.ac.kr/KNU/16927/subview.do',
      },
    ],
  },
];

// 미리보기 기능 변수 선언
const previewArea = document.getElementById('preview-area');
let showPreviewTimer;
let hidePreviewTimer;

// 초기 렌더링 및 날짜 입력 필드 설정
document.addEventListener('DOMContentLoaded', () => {
  const noticeDateInput = document.getElementById('notice-date-input');
  const today = new Date();

  // 오늘 날짜를 YYYY-MM-DD 형식으로 포맷
  const todayFormatted = formatDate(today);
  
  // 날짜 필터
  const pastDate = new Date();
  pastDate.setDate(pastDate.getDate() - 4); // 최대 5일까지
  const pastDateFormatted = formatDate(pastDate);

  noticeDateInput.value = todayFormatted; // 기본값은 오늘 날짜
  noticeDateInput.max = todayFormatted; // 최대 선택 가능 날짜를 오늘로 설정
  noticeDateInput.min = pastDateFormatted; // 최소 선택 가능 날짜를 4일 전으로 설정

  renderNoticeList(todayFormatted); // 페이지 로드 시 기본값으로 오늘 공지사항 렌더링

  noticeDateInput.addEventListener('change', (event) => {
    renderNoticeList(event.target.value); // 선택된 날짜로 공지사항 렌더링
  });
});

// 마우스가 게시판 목록으로 들어왔을 때
document.addEventListener('mouseover', async (event) => {
  const target = event.target.closest('.notice-item');
  if (!target) return; // 게시판 목록에 마우스 없으면 종료

  const boardUrl = target.href; // 게시판 URL 가져오기
  const boardTitle = target.querySelector('.notice-title').textContent; // 게시판 제목 가져오기

  // 미리보기 창이 이미 열려있고 같은 URL이라면 로딩x
  if (previewArea.style.display !== 'none' && previewArea.dataset.url === boardUrl) {
    return;
  }

  // 기존 미리보기 숨김 타이머가 있다면 취소
  clearTimeout(hidePreviewTimer);

  // 미리보기 표시 타이머 설정 (마우스를 바로바로 움직이면 미리보기 로직이 꼬이는 문제 해결)
  showPreviewTimer = setTimeout(async () => {
    // 미리보기 띄우기
    previewArea.innerHTML = `<h3>${boardTitle}</h3><p>로딩 중...</p>`;
    previewArea.style.display = 'flex';
    previewArea.style.position = 'absolute';
    previewArea.dataset.url = boardUrl; // 현재 미리보기 중인 URL 저장
    const noticeCount = parseInt(target.dataset.count, 10); // 새 공지 개수 가져오기

    // 새 공지 없으면 미리보기 표시x
    if (noticeCount === 0) {
      previewArea.style.display = 'none';
      previewArea.dataset.url = ''; // URL 데이터 초기화
      return;
    }

    // 마우스 위치에 따라 미리보기 위치 설정
    const mouseX = event.clientX;
    const mouseY = event.clientY;
    const offsetX = 20;
    const offsetY = 20;
    previewArea.style.left = `${mouseX + offsetX}px`;
    previewArea.style.top = `${mouseY + offsetY}px`;

    // 미리보기 창 구현
    try {
      const selectedDateInput = document.getElementById('notice-date-input');
      const selectedDateString = selectedDateInput.value; // 선택된 날짜 문자열 가져오기

      // Django API 호출로 미리보기 데이터 가져오기
      const response = await fetch(`/api/notice-preview/?url=${encodeURIComponent(boardUrl)}&date=${selectedDateString}`);
      if (!response.ok) {
        throw new Error('API 호출 실패');
      }
      const data = await response.json();

      let previewContent = `<h3>${data.board_name}</h3><ul>`;

      // 미리보기에 새 공지 제목 삽입
      if (data.notices && data.notices.length > 0) {
        data.notices.forEach(notice => {
          previewContent += `<li>${notice.title}</li>`;
        });
      }
      previewContent += `</ul>`;
      previewArea.innerHTML = previewContent;

    } catch (e) {
      console.error('미리보기 내용을 가져오는 중 오류 발생:', e);
      previewArea.innerHTML = `<h3>${boardTitle}</h3><p>미리보기를 로딩할 수 없습니다.</p>`;
    }
  }, 200); // 0.2초 후 미리보기 표시
});

// 마우스가 게시판 목록 밖으로 이동했을 때
document.addEventListener('mouseout', (event) => {
  const target = event.target.closest('.notice-item');
  if (!target) return; // 게시판 목록 창 근처가 아닌 경우 종료

  clearTimeout(showPreviewTimer); // 미리보기 표시 타이머 취소

  // 미리보기 숨김 타이머 설정
  hidePreviewTimer = setTimeout(() => {
    previewArea.style.display = 'none';
    previewArea.dataset.url = '';
  }, 200);
});

// 날짜 YYYY-MM-DD 형식으로 포맷
function formatDate(date) {
  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, '0'); // 한자리일 경우 두자리로 표시
  const day = date.getDate().toString().padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// 게시판 URL과 필터 날짜에 따라 공지를 크롤링하고 필터링
async function crawlAndFilterNotices(boardUrl, filterDate) {
  const filteredNotices = [];
  let page = 1;

  while (true) {
    try {
      const pageUrl = page === 1 ? boardUrl : `${boardUrl}?page=${page}`;
      const proxyUrl = `/proxy?url=${encodeURIComponent(pageUrl)}`;
      const res = await fetch(proxyUrl); // 크롤링할 사이트 url을 proxy.js에게 전달
      const html = await res.text(); // proxy.js 서버로부터 응답
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');

      const noticeRows = doc.querySelectorAll('tr:not(.notice)'); // 고정된 공지가 아닌 행 추출

      // 공지가 없으면 중단
      if (noticeRows.length === 0) {
        break;
      }

      let stopCrawling = false;

      for (const row of noticeRows) {
        const dateCell = row.querySelector('.td-date'); // 게시글 날짜 가져오기
        const titleElement = row.querySelector('td a'); // 게시글 제목 가져오기

        if (!dateCell || !titleElement) continue;

        let dateStr = dateCell.textContent.trim(); // 날짜를 String으로
        dateStr = dateStr.replace(/\./g, '-'); // YYYY.MM.DD -> YYYY-MM-DD 형식으로
        const noticeDate = new Date(dateStr);
        noticeDate.setHours(0, 0, 0, 0);

        // 공지 날짜가 지정된 날짜보다 이전이면 중단
        if (noticeDate < filterDate) {
          stopCrawling = true;
          break;
        }

        // 날짜 일치 여부 비교
        if (noticeDate.getFullYear() === filterDate.getFullYear() &&
            noticeDate.getMonth() === filterDate.getMonth() &&
            noticeDate.getDate() === filterDate.getDate()) {
          filteredNotices.push({ title: titleElement.textContent.trim(), url: titleElement.href });
        }
      }

      // 지정한 날짜가 페이지에 없으면 나가기
      if (stopCrawling) {
        break;
      }

      page++; // 다음 페이지로 이동

    } catch (e) {
      console.error("Crawling Error", e);
      break;
    }
  }
  return filteredNotices;
}

// 선택한 날짜의 공지 갯수 카운팅하는 함수
async function fetchNoticeCount(board, targetDateStr = null) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  let filterDate = today; // 기본값은 오늘
  if (targetDateStr) { // 날짜 선택 시
    filterDate = new Date(targetDateStr);
    filterDate.setHours(0, 0, 0, 0);
  }

  const notices = await crawlAndFilterNotices(board.url, filterDate);
  return notices.length; // 개수 반환
}

// 여러 게시판의 공지사항 개수를 가져와서 웹 페이지에 동적으로 렌더링하는 함수
async function renderNoticeList(dateString = null) {
  // 공지사항과 곰나루광장의 게시판 목록 요소 찾기
  const noticeBoardListContainer = document.querySelector('#notice-category-section .board-list');
  const gomnaruBoardListContainer = document.querySelector('#gomnaru-category-section .board-list');

  // 로딩 메시지 표시
  noticeBoardListContainer.innerHTML = '<p>로딩 중...</p>';
  gomnaruBoardListContainer.innerHTML = '<p>로딩 중...</p>';

  try {
    const today = new Date();
    const filterDate = dateString ? new Date(dateString) : today;
    const dateStr = formatDate(filterDate);
    
    // Django API 호출로 모든 데이터 한번에 가져오기
    const response = await fetch(`/api/notice-counts/?date=${dateStr}`);
    if (!response.ok) {
      throw new Error('API 호출 실패');
    }
    const data = await response.json();
    
    // 각 카테고리별로 렌더링
    data.categories.forEach(category => {
      const targetContainer = category.name === '공지사항' ? 
        noticeBoardListContainer : gomnaruBoardListContainer;
      
      targetContainer.innerHTML = '';
      
      category.boards.forEach((board, index) => {
        const item = document.createElement('a');
        item.className = 'notice-item';
        item.href = board.url;
        item.target = '_blank';
        item.dataset.count = board.count;
        item.innerHTML = `
          <span class="notice-title">${board.name}</span>
          <span class="notice-count">${board.count}</span>  
        `;
        
        if (board.count === 0) {
          item.classList.add('inactive-notice-item');
        }
        
        item.style.opacity = '0';
        targetContainer.appendChild(item);
        
        // 애니메이션
        setTimeout(() => {
          item.style.opacity = '1';
          item.style.animation = `fadeIn 0.5s ease-out forwards`;
        }, 50 * index);
      });
    });
    
  } catch (error) {
    console.error('공지사항 목록 로딩 실패:', error);
    noticeBoardListContainer.innerHTML = '<p>데이터 로딩 실패</p>';
    gomnaruBoardListContainer.innerHTML = '<p>데이터 로딩 실패</p>';
  }
}