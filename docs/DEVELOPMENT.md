# 개발·인증·API 참고

소스 설치, 인증 파일, MCP 클라이언트 설정, 확인한 API 계약, 개발·검증 절차를 다룹니다.

## 개발자용 소스 설치

Python 3.11 이상과 [uv](https://docs.astral.sh/uv/)가 필요합니다.

```bash
git clone https://github.com/dadadamarine/runnerpoker-mcp.git
cd runnerpoker-mcp
uv sync --frozen
uv run runnerpoker-mcp
```

마지막 명령은 MCP 클라이언트의 표준 입력을 기다립니다.

## 인증

브라우저에서 본인 계정으로 `https://craft.runnerpoker.com/ko/timeline`에 로그인합니다.
개발자 도구에서 해당 사이트의 Local Storage를 확인하세요.

- `accessToken`: access token
- `auth-storage` → `state.user.userSeq`: 사용자 번호

이 두 값을 담은 JSON을 **채팅·GitHub·명령행 인자에 올리지 말고**, 로컬 JSON 파일로
준비한 뒤 다음 명령의 표준 입력으로 전달하세요. 인증 파일은 저장소 밖에 두세요.

```bash
uv run runnerpoker-auth < /absolute/path/to/private-session.json
```

입력 형식은 `{"accessToken":"YOUR_TOKEN","userSeq":123}` 입니다.
기본 저장 위치는 `~/.config/runnerpoker-mcp/credentials.json`이며 권한은 `0600`입니다.
`RUNNERPOKER_AUTH_FILE` 환경변수로 경로를 바꿀 수 있습니다. 요청마다 다시 읽으므로
토큰을 교체할 때 서버를 재시작할 필요가 없습니다.
만료된 세션은 브라우저에서 다시 로그인한 후 갱신하세요. 자동 로그인·refresh는 구현하지 않았습니다.

### 에이전트의 로컬 Chrome 인증 추출

사용자가 본인 브라우저에서 인증 정보를 추출해 MCP에 저장하도록 요청한 경우,
에이전트가 로컬 저장소를 읽어 위 인증 명령의 표준 입력으로 전달할 수 있습니다.
토큰을 사용자가 채팅에 붙여넣도록 요청하거나 개발자 콘솔에 출력하지 마세요.

macOS Chrome의 기본 프로필 저장소는
`~/Library/Application Support/Google/Chrome/Default/Local Storage/leveldb`입니다.
다른 프로필을 사용하는 경우 Chrome의 `Local State`에서 프로필을 확인하세요.

1. 저장소를 읽기 전용으로 열고 `https://craft.runnerpoker.com` origin의
   `accessToken`과 `auth-storage` 값만 선택합니다.
2. LevelDB 레코드의 sequence와 삭제 기록을 반영해 현재 값을 판별합니다.
   오래된 토큰이 섞일 수 있으므로 파일 전체의 단순 문자열 검색 결과를 사용하지 마세요.
   로그만으로 현재 값을 확정할 수 없으면 SST 테이블까지 처리하는 리더가 필요합니다.
3. `auth-storage` JSON의 `state.user.userSeq`를 읽고, 토큰과 함께 메모리에서
   JSON을 구성해 `runnerpoker-auth`의 표준 입력으로 전달합니다.
   토큰은 콘솔·채팅·명령행 인자·로그·저장소·중간 파일에 남기지 않습니다.
4. `auth_status`에서 `configured: true`를 확인한 뒤,
   `get_timeline(page=1, page_size=1)` 같은 소량의 읽기 요청이 성공하는지 확인합니다.
   `auth_status`만으로 원격 인증 성공을 판단하지 마세요.

이 경로는 Chrome 저장 형식에 의존하는 수동 운영 절차이며, 프로젝트에 자동 추출
명령은 아직 없습니다. 브라우저 원본 저장소를 수정하거나 잠금 파일을 제거하지 마세요.
저장소에서 값을 찾지 못하거나 원격 인증이 만료되면 사용자에게 브라우저 재로그인을
요청하고 다시 추출합니다. MCP 서버 재시작은 필요하지 않습니다.

## MCP 클라이언트 설정

클라이언트의 stdio 서버 설정에 다음 command와 args를 사용하세요.
경로는 실제 clone 위치에 맞게 수정합니다. 환경변수는 기본 인증 경로를 쓰면 생략합니다.

```json
{
  "mcpServers": {
    "runnerpoker": {
      "command": "uv",
      "args": ["run", "--frozen", "--directory", "/absolute/path/to/runnerpoker-mcp", "runnerpoker-mcp"],
      "env": {"RUNNERPOKER_AUTH_FILE": "/absolute/path/to/private/credentials.json"}
    }
  }
}
```

이 프로젝트는 클라이언트 설정을 자동 변경하지 않습니다.

## 확인한 API 계약과 한계

- 원본 페이지: https://craft.runnerpoker.com/ko/timeline
- 호스트: `https://api.runnerpoker.com`
- `GET /api/v1/craft/timeline?Period=today&Page=1&PageSize=10`
- 사용자 지정 기간: `Period=custom&From=YYYY-MM-DD&To=YYYY-MM-DD`
- `GET /api/v1/craft/timeline/{YYYY-MM-DD}`
- 헤더: `Authorization: Bearer …`, `X-User-Seq: …`
- 프런트엔드가 참조하는 목록 응답: `performance`, `days.items`, `days.totalPages`
- 상세 응답: `items`
- 핸드 목록: `GET /hand-histories` (`GameType`, `ParticipantId`, `From`, `To`,
  `Cursor`, `PageSize`); 응답 `items`, `hasNext`, `nextCursor`
- 핸드 상세: `GET /hand-histories/v2/{handId}`; `players`, `table`, `streets`, `pots`

2026-11-07에 공개 웹앱 JavaScript에서 경로·인자·헤더와 무인증 요청의 `401`을
확인했습니다. 이후 본인 계정으로 타임라인·핸드 목록/상세·세션 성과·파켓페어 집계를
실제 조회했습니다. 이 검증이 모든 API·액션 기록의 완전성을 보장하지는 않습니다.
필드 의미·단위와 API 안정성은 공식 문서로 보장되지 않습니다.
위 응답 구조는 프런트엔드 사용 코드에서 확인한 것이며, 가짜 성공 응답을 실제 데이터로
취급하지 않습니다. 테스트 fixture는 합성 데이터입니다.

자격 증명은 고정된 API 호스트에만 보내며 리다이렉트를 따라가지 않습니다.
서버에는 POST·베팅·계정 변경·임의 URL 호출 도구가 없습니다. HTTP 오류 본문은 도구 오류에
포함하지 않습니다. 상류 API 변경 시 수정이 필요할 수 있습니다.

## 개발 및 검증

```bash
uv sync --frozen
uv run ruff check .
uv run coverage run -m pytest -q
uv run coverage report
```

HTTP 모킹으로 헤더·날짜·페이지·오류 처리를 검증하며, 실제 stdio 프로세스를 띄워
MCP initialize → tools/list → tools/call까지 검사합니다. CI는 인증 정보 없이 실행합니다.
CI는 라인·분기 커버리지를 측정하고 합산 80% 미만이면 실패합니다.

### PokerStars 변환 서브패키지

`src/runnerpoker_mcp/pokerstars/`는 표준 라이브러리만 쓰는 독립 모듈입니다. MCP 서버·HTTP
클라이언트·인증 코드를 import하지 않으며(`tests/pokerstars/test_independence.py`가 강제),
오류는 자체 `ConversionError`로 냅니다. 다른 프로젝트에서 쓰려면 이 디렉터리만 복사하면 됩니다.

```python
from runnerpoker_mcp.pokerstars import ConversionError, export_warnings, to_pokerstars

text = to_pokerstars(record, hero_id=9396, bb_units=False)  # record = get_hand_history 응답
warnings = export_warnings(record)  # 버튼-SB 좌석 불일치 등 변환을 막지 않는 경고
```

| 파일 | 책임 |
|---|---|
| `converter.py` | 레코드 → PokerStars 텍스트 (액션·팟·uncalled·요약) |
| `cards.py` | Craft 카드 id(1~52) → `As`, `Td` 표기 |
| `validation.py` | 중복 카드·히어로 카드 수 검증, 버튼-SB 경고 (locktree export 검증 규칙) |
| `errors.py` | `ConversionError` |

실제 핸드 레코드 픽스처와 검토를 마친 골든 출력은 `tests/pokerstars/fixtures/`에 있습니다.

`tests/fixtures/responses.json`은 **실계정에서 캡처한 응답이 아닌 합성 fixture**입니다.
공개 프런트엔드에서 확인한 구조를 바탕으로 작성했고 개인정보·실제 토큰은 포함하지 않습니다.
상류 API의 실제 성공 응답과 완전히 같다고 보장하지 않습니다.

`tests/test_functional.py`는 SDK의 실제 MCP 메시지 연결·도구 스키마·JSON 결과 직렬화를
사용하고 HTTP 경계만 `httpx.MockTransport`로 대체합니다. fixture router가 처리하지 않는
요청은 실패하므로 이 기능 테스트에서 인터넷 API로 빠져나가지 않습니다.

검증 시나리오:

- 14개 도구 전체의 정상 호출과 결과 파싱
- 파켓페어+3벳 팟+리버+손실 검색, 4벳 제외, 프리플랍·플랍·턴 올인 런아웃
- 페이지 커서·중복 제거·반복 커서 중단·조회 예산·결과 잘림 표시
- 기간·채널·포지션 필터, 한국 날짜 → UTC 시각, 원본 HUD 비율·사이트 용어 유지
- 핸드 레인지 손익 집계 → 실제 액션 기록 일괄 조회의 연결
- 잘못된 JSON·응답 루트·누락 필드·핸드 ID 불일치·잘못된 액션·미확인 그룹
- HTTP 302/401/403/404/429/500·타임아웃·부분 실패와 오류 본문/토큰 노출 방지
- 전체 1,326 홀카드 조합 → 169클래스 및 6/4/12 콤보 수 검증

SDK: https://github.com/modelcontextprotocol/python-sdk/tree/v1.x

## 추가로 확인한 사이트 기능

2026-11-07 공개 페이지·배포 JS에서 확인한 호출입니다. 아래 항목은 아직 MCP 도구로
구현하지 않았으며 인증된 응답을 검증하지 않았습니다. 경로는 고정 API 호스트 기준입니다.

| 기능 | API 경로 |
|---|---|
| 수익 곡선·다운스윙 | `/api/v1/craft/holdem/{profit-curve,downswing}` |
| 최근 결과·세션 하이라이트 | `/api/v1/craft/holdem/{recent-results,session-highlights}` |
| 채널별 통계·채널 목록 | `/api/v1/craft/holdem/channels/summary`, `/api/v1/craft/holdem/channels` |
| 토너먼트 요약·수익·기록·단계 | `/api/v1/craft/tournament/{summary,profit-curve,downswing,recent-results,records,stages}` |
| 토너먼트 선택·전략·참가 기록 | `/api/v1/craft/tournament/{configs,strategies,entries}` |
| 챌린지 목록·상세·곡선 | `/api/v1/craft/challenges`, `/api/v1/craft/challenges/{id}`, `/api/v1/craft/challenges/{id}/curve` |

레인지 매트릭스는 핸드 목록의 Hero 홀카드를 프런트엔드에서 169개 클래스별로 묶어
표시합니다. 챌린지 생성·포기 POST 호출도 발견했으나 읽기 전용 MCP에는 노출하지 않습니다.
