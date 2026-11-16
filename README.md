# RunnerPoker MCP

러너포커 Craft의 **내 기록을 AI에게 물어볼 수 있게 연결하는 프로그램**입니다.
설치한 뒤 “최근 세션 보여줘”, “이번 달 파켓페어 손익을 비교해줘”처럼 요청하면
AI가 본인 계정의 기록과 통계를 조회합니다. 러너포커가 만든 공식 프로그램은 아닙니다.

**내 컴퓨터에서 실행하는 읽기 전용 MCP**입니다. MCP는 AI 앱이 외부 도구를 사용하는
연결 방식입니다. 베팅·입출금·계정 변경은 하지 않으며, GTO 솔버도 실행하지 않습니다.

## 할 수 있는 일

| 기능 | 내용 | 도구 |
|---|---|---|
| 타임라인 | 기간별 플레이 타임라인과 성과, 특정 날짜의 상세 이벤트 | `get_timeline`, `get_timeline_day` |
| 세션 | 기간별 세션 목록, 세션 성과와 스택 추세 | `list_holdem_sessions`, `get_session_performance` |
| 핸드 히스토리 | 세션·날짜별 핸드 목록, 핸드 원본 기록(플레이어·보드·액션·사이징·팟), 1–30개 일괄 조회 | `list_hand_histories`, `get_hand_history`, `get_hand_histories` |
| PokerStars 내보내기 | 핸드를 PokerStars 핸드 히스토리 텍스트로 변환하고 내 컴퓨터 클립보드에 복사(복사는 macOS) | `get_hand_history_pokerstars` |
| 통계 | 홀덤 요약과 HUD(VPIP·PFR·3Bet 등), 포지션별 통계, 핸드 클래스별(AA·AKs·AKo) 손익 | `get_holdem_summary`, `get_hud_stats`, `get_position_stats`, `get_hand_range_stats` |
| 핸드 리뷰 | 파켓페어·3벳 팟·리버 참여·수익/손실 조건으로 핸드 검색, 포지션·핸드 클래스·팟 유형별 표본 집계 | `search_review_hands`, `summarize_review_spots` |
| 연결 확인 | 로컬 인증 파일의 설정 여부 확인 | `auth_status` |

러너포커 계정과 기록은 조회만 합니다. 서버가 수행하는 유일한 쓰기는 PokerStars 텍스트의
클립보드 복사입니다. 도구 인자와 판정 로직은 [도구 상세](docs/TOOLS.md)에 있습니다.

## 지원 앱

| 앱 | 연결 방법 |
|---|---|
| Claude 데스크톱 앱 | 앱의 로컬 MCP 설정에 실행 명령 추가 — [안내](docs/INSTALL.md#4-a-claude-데스크톱-앱-연결하기) |
| Claude Code | 저장소 마켓플레이스 또는 MCP 직접 추가 — [안내](docs/INSTALL.md#4-b-claude-codecodex-마켓플레이스-설치) |
| Codex | 저장소 마켓플레이스 또는 MCP 직접 추가 — [안내](docs/INSTALL.md#4-b-claude-codecodex-마켓플레이스-설치) |
| ChatGPT 데스크톱 앱 | 로컬 플러그인 메뉴가 있는 환경에서 설치. 앱 안의 도구 사용은 미검증 — [안내](docs/INSTALL.md#4-c-chatgpt-데스크톱-앱) |

데스크톱 앱 전용이며, 웹브라우저에서 여는 ChatGPT와 Claude는 지원 대상 밖입니다.
안내는 macOS 기준입니다. 저장소 주소로 추가하는 커뮤니티 배포이고 공식 마켓 등재 전입니다
([배포 상태](docs/DISTRIBUTION.md)).

## 빠른 시작

Mac의 터미널 앱에서 진행합니다. Git과
[uv](https://docs.astral.sh/uv/getting-started/installation/)가 필요합니다.

1. 프로그램을 받습니다.

   ```bash
   mkdir -p "$HOME/Applications"
   git clone https://github.com/dadadamarine/runnerpoker-mcp.git "$HOME/Applications/runnerpoker-mcp"
   cd "$HOME/Applications/runnerpoker-mcp"
   uv sync --frozen --python 3.11
   ```

2. Chrome에서 [러너포커 Craft](https://craft.runnerpoker.com/ko/timeline)에 로그인하고
   [계정을 연결](docs/INSTALL.md#3-러너포커-계정-연결하기)합니다.
   인증 토큰과 비밀번호는 채팅에 붙여넣지 마세요.

3. 사용하는 앱에 연결합니다. Claude Code는 대화 안에서 실행합니다.

   ```text
   /plugin marketplace add dadadamarine/runnerpoker-mcp
   /plugin install runnerpoker@runnerpoker-community
   ```

   Codex는 터미널에서 실행합니다.

   ```bash
   codex plugin marketplace add dadadamarine/runnerpoker-mcp
   codex plugin add runnerpoker@runnerpoker-community
   ```

   Claude 데스크톱 앱과 ChatGPT 데스크톱 앱은 위 **지원 앱** 표의 안내를 따릅니다.

4. 연결한 앱의 새 대화에서 확인합니다.

   > 러너포커 연결 상태를 확인하고 최근 세션 하나를 조회해줘.

단계별 설명은 [설치와 연결 가이드](docs/INSTALL.md)에, 오류별 해결 방법은
[연결이 안 될 때](docs/INSTALL.md#7-연결이-안-될-때)에 있습니다.

## 이렇게 물어보세요

| 하고 싶은 일 | 복사해서 사용할 요청 |
|---|---|
| 오늘 기록 확인 | 오늘 플레이 요약과 세션 목록을 보여줘. |
| 기간 지정 | 2026년 11월 1일부터 7일까지 홀덤 요약을 보여줘. |
| 파켓페어 비교 | 최근 7일 AA부터 22까지 손익과 핸드 수를 보여줘. 실제 조회 범위와 표본 부족도 표시해줘. |
| 한 세션 복기 | 최근 마스터 세션 하나를 찾아서, 그 세션의 파켓페어 손익을 비교해줘. |
| 손실 복기 | 그 세션에서 50BB 이상 잃은 파켓페어 핸드 3개를 찾아 당시 정보만으로 리뷰해줘. |
| 결과 편향 줄이기 | 같은 조건에서 이긴 핸드도 같이 비교해줘. 진 결과만으로 실수라고 판단하지 마. |
| 핸드 내보내기 | 가장 최근 핸드를 PokerStars 형식으로 가져와줘. |

BB 단위, 채널 구분, 조회 범위처럼 결과를 읽을 때 알아둘 점은
[설치 가이드 6단계](docs/INSTALL.md#6-이렇게-물어보세요)에 있습니다.

## 문서

| 문서 | 내용 |
|---|---|
| [설치와 연결 가이드](docs/INSTALL.md) | 앱별 설치 단계, 계정 연결, 첫 조회, 문제 해결 |
| [도구 상세](docs/TOOLS.md) | 도구 인자, 핸드 검색과 판정 로직, 통계 도구 |
| [개발·인증·API 참고](docs/DEVELOPMENT.md) | 소스 설치, 인증 파일, MCP 클라이언트 설정, 확인한 API 계약, 테스트 |
| [배포 경로와 검증 상태](docs/DISTRIBUTION.md) | 마켓플레이스 패키지와 공식 등재 상태 |
