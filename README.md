# RunnerPoker MCP

러너포커 Craft의 **내 기록을 AI에게 물어볼 수 있게 연결하는 프로그램**입니다.
설치한 뒤 “최근 세션 보여줘”, “이번 달 파켓페어 손익을 비교해줘”처럼 요청하면
AI가 본인 계정의 기록과 통계를 조회합니다. 러너포커가 만든 공식 프로그램은 아닙니다.

**내 컴퓨터에서 실행하는 읽기 전용 MCP**입니다. MCP는 AI 앱이 외부 도구를 사용하는
연결 방식입니다. 베팅·입출금·계정 변경은 하지 않으며, GTO 솔버도 실행하지 않습니다.

## 처음 사용하는 분께

### 코딩을 몰라도 따라 하는 빠른 안내

아래 순서대로 진행하면 됩니다. 화면에 보이는 메뉴 이름은 앱 버전이나 macOS 언어에 따라
다를 수 있습니다. 막히면 아래의 **연결이 안 될 때** 표에서 오류 문구를 찾아보세요.

1. [러너포커 Craft에 로그인](https://craft.runnerpoker.com/ko/timeline)합니다. Chrome을
   사용하는 것을 권장합니다.
2. 사용하는 앱에 맞춰 연결합니다. **Claude 데스크톱 앱**은 아래 4-A, **Codex 데스크톱 앱**은
   4-B의 Codex 방법, **Claude Code**는 4-B의 Claude Code 방법을 따라가세요.
   ChatGPT 데스크톱 앱은 로컬 플러그인 메뉴가 보일 때만 4-C를 진행합니다.
3. 연결한 앱의 새 대화에서 아래 문장을 복사해 보냅니다.

   > 러너포커 연결 상태를 확인하고 최근 세션 하나를 조회해줘.

4. 인증 오류가 나오면 오류에 표시된 **Craft 로그인 링크**를 열어 다시 로그인한 다음,
   같은 앱 대화에서 **“러너포커 연결을 갱신해줘”**라고 요청합니다. 컴퓨터의 Chrome 인증을
   읽을 수 있는 앱 환경이라면 에이전트가 로컬 연결 정보도 갱신합니다. 지원하지 않는 환경은
   화면에 다음 조치를 안내합니다.

처음 한 번은 컴퓨터에 연결 프로그램을 설치하고 앱에 연결해야 합니다. 이 저장소는
**설치 파일을 내려받아 실행하는 일반 앱 설치 프로그램이 아니라**, 아래 단계에 따라 로컬
연결을 준비하는 방식입니다. 명령어 입력이 부담스럽다면 컴퓨터에 접근할 수 있는 AI 도우미에게
“이 README의 처음 사용하는 분께 절차대로 RunnerPoker를 설치하고, 중간에 필요한 화면을
차례대로 안내해줘”라고 요청하세요. 인증 토큰이나 비밀번호를 채팅에 붙여넣지 마세요.

설치 흐름은 **준비 → 프로그램 받기 → 계정 연결 → 데스크톱 앱 연결 → 첫 조회**입니다.
브라우저 로그인과 AI 앱 연결은 별도 단계입니다.

| 사용하려는 앱 | 연결 방법 | 확인 상태 |
|---|---|---|
| Claude 데스크톱 앱 | 앱의 로컬 MCP 설정에 실행 명령 추가 | 앱에서 실행 중 상태 및 일반 채팅의 실제 인증·타임라인 조회 확인 |
| Claude Code | 저장소 마켓플레이스 또는 MCP 직접 추가 | 플러그인 manifest 검증. Claude 앱과는 별도 설치 |
| Codex | 저장소 마켓플레이스 또는 MCP 직접 추가 | 로컬 플러그인 설치 및 실행 명령의 인증 조회 확인 |
| ChatGPT 데스크톱 앱 | 로컬 플러그인을 지원하는 앱 환경에서 설치 | 패키지 준비. ChatGPT 앱 내 도구 사용은 미검증 |
| 웹 ChatGPT·웹 Claude | 현재 로컬 실행 방식으로 직접 연결하지 않음 | 원격 서버·인증 연동은 미구현 |

ChatGPT 앱이라고 해서 일반 채팅에서 로컬 MCP 설정 파일을 바로 읽는다고 보장하지
않습니다. 로컬 플러그인 지원 환경과 로컬 실행 대화가 필요합니다.
**공식 마켓에 등재된 상태는 아닙니다.** [배포 상태](#마켓플레이스와-chatgpt-배포-상태)를 확인하세요.

### 1. 준비하기 — macOS 기준

- 본인 러너포커 계정과 [Craft](https://craft.runnerpoker.com/ko/timeline) 로그인
- 연결할 Claude 앱 또는 Codex 등의 MCP 지원 앱
- 프로그램을 받는 Git과 실행 도구 [uv](https://docs.astral.sh/uv/getting-started/installation/)

아래 명령은 AI 채팅이 아닌 **Mac의 터미널 앱**에서 실행합니다.
Spotlight에서 `터미널`을 검색해 열고, 코드 블록 안의 명령만 복사하세요.
`$` 같은 표시를 앞에 붙일 필요는 없습니다.

Git과 uv가 있는지 확인합니다.

```bash
git --version
uv --version
```

버전 번호가 나오면 다음 단계로 갑니다. Git 설치 안내가 뜨면 macOS 안내에 따라
설치합니다. uv가 없다면 [공식 설치 안내](https://docs.astral.sh/uv/getting-started/installation/)를
따르세요. macOS 공식 설치 명령은 다음과 같습니다.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

설치 후 터미널을 새로 열고 `uv --version`을 다시 실행합니다.
Python은 다음 단계에서 uv가 3.11을 설치하도록 지정하므로 별도 설치하지 않아도 됩니다.
이 문서의 데스크톱 앱 연결은 macOS 기준이며, Windows 앱에서의 동작은 검증하지 않았습니다.

### 2. 프로그램 받기

```bash
mkdir -p "$HOME/Applications"
git clone https://github.com/dadadamarine/runnerpoker-mcp.git "$HOME/Applications/runnerpoker-mcp"
cd "$HOME/Applications/runnerpoker-mcp"
uv sync --frozen --python 3.11
```

이후 명령은 위 `runnerpoker-mcp` 폴더에서 실행합니다.
이미 같은 폴더에 설치했다면 다시 clone하지 말고 그 폴더로 이동하세요.
설치 폴더를 삭제하거나 옮기면 그 경로를 참조하는 앱 설정도 수정해야 합니다.

### 3. 러너포커 계정 연결하기

먼저 Chrome에서 [Craft 타임라인](https://craft.runnerpoker.com/ko/timeline)에 로그인합니다.

**로컬 파일에 접근할 수 있는 AI 에이전트가 있다면** 다음 문장을 요청할 수 있습니다.

> 본인 러너크래프트 계정을 이 컴퓨터의 RunnerPoker MCP에 연결해줘.
> README의 로컬 Chrome 인증 추출 절차로 해당 사이트의 accessToken과 userSeq만 읽고,
> 토큰을 콘솔·채팅·로그에 출력하지 말고 로컬 인증 파일에 저장해줘.
> 저장 후 auth_status와 실제 타임라인 조회를 모두 확인해줘.

자동 추출 명령이 내장된 것은 아닙니다. 에이전트에 로컬 파일 접근 기능이 없거나
현재 저장 형식을 읽지 못하면 아래 수동 방법을 사용합니다. 브라우저에 로그인되지
않았거나 세션이 만료됐으면 먼저 본인이 다시 로그인해야 합니다.

<details>
<summary>직접 연결하기: Chrome 화면에서 값 확인 → 터미널에 비공개 입력</summary>

1. Craft 탭에서 Chrome 메뉴 → 보기 → 개발자 정보 → 개발자 도구를 엽니다.
2. 개발자 도구의 **Application** 탭을 선택합니다. 안 보이면 탭의 `»` 메뉴를 확인합니다.
3. 왼쪽 **Storage → Local Storage → https://craft.runnerpoker.com**을 선택합니다.
4. `accessToken` 행의 Value를 복사합니다. 쿠키의 `_ga`, `_fbp`,
   `auth-session-active`는 MCP 인증 토큰이 아닙니다.
5. `auth-storage` 행의 JSON에서 `state → user → userSeq` 숫자도 확인합니다.
6. 아래 명령을 터미널에서 실행합니다. 첫 입력에 토큰을 붙여넣고 Enter,
   두 번째 입력에 사용자 번호를 입력합니다. 토큰을 입력할 때 글자가 보이지 않는 게 정상입니다.

```bash
uv run --frozen python -c '
import getpass, json, subprocess, sys
if not sys.stdin.isatty():
    raise SystemExit("대화형 터미널에서 실행하세요.")
token = getpass.getpass("accessToken (화면에 표시되지 않음): ")
seq = input("userSeq (숫자): ").strip()
if not seq.isdecimal() or int(seq) <= 0:
    raise SystemExit("userSeq는 양의 정수여야 합니다.")
result = subprocess.run(
    ["uv", "run", "--frozen", "runnerpoker-auth"],
    input=json.dumps({"accessToken": token, "userSeq": int(seq)}), text=True
)
raise SystemExit(result.returncode)
'
```

`RunnerPoker credentials saved (mode 0600).`이 나오면 저장됐습니다.
기본 저장 위치는 `~/.config/runnerpoker-mcp/credentials.json`입니다.
이 파일은 비밀번호처럼 취급하고 공유하지 마세요. 개발자 도구의 Console에서 토큰을
출력하거나 AI 채팅·이슈·스크린샷에 붙여넣지 않습니다. 복사한 뒤 클립보드에는 다른
일반 텍스트를 복사해 두세요. 개발자 도구를 닫아도 됩니다.

</details>

### 4-A. Claude 데스크톱 앱 연결하기

**Claude Code 플러그인을 설치하는 것과 다른 절차입니다.**

1. Claude 앱의 설정에서 **Developer → Edit Config**를 엽니다.
   앱 버전에 따라 **Desktop app → Extensions → Manage → Local MCP servers**에
   로컬 서버 상태가 표시됩니다.
2. 터미널에서 다음 명령으로 uv 위치와 설치 폴더 경로를 확인합니다.

```bash
command -v uv
pwd
```

3. 설정 파일을 연 뒤 **Claude 앱을 완전히 종료한 상태에서** 편집합니다.
   실행 중 편집하면 앱 종료 시 메모리에 있던 설정이 파일을 덮어쓸 수 있습니다.
   설정 파일의 `mcpServers` 안에 `runnerpoker`를 추가합니다.
   기존 설정과 다른 서버는 보존하세요. 아래의 두 예시 경로를 위 출력으로 바꿉니다.

```json
{
  "mcpServers": {
    "runnerpoker": {
      "command": "/Users/YOUR_NAME/.local/bin/uv",
      "args": [
        "run", "--frozen", "--directory",
        "/Users/YOUR_NAME/Applications/runnerpoker-mcp",
        "runnerpoker-mcp"
      ]
    }
  }
}
```

4. 저장 후 Claude 앱을 완전히 종료하고 다시 엽니다. 창만 닫는 것과 앱 종료는 다릅니다.
5. 새 대화의 **+ → Connectors** 또는 로컬 MCP 서버 설정에서 `runnerpoker`를 확인합니다.
   [첫 조회](#5-첫-조회와-연결-확인)의 문장을 입력하세요.

macOS 설정 파일은 `~/Library/Application Support/Claude/claude_desktop_config.json`입니다.
앱에서 `uv`를 못 찾는 문제를 피하려고 `command`에는 **전체 경로**를 사용합니다.
서버를 터미널에서 계속 켜둘 필요는 없습니다. 앱이 실행 명령으로 서버를 시작합니다.
공식 안내: [Claude 로컬 서버 연결](https://modelcontextprotocol.io/docs/develop/connect-local-servers),
[Claude 데스크톱 확장 관리](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop).

### 4-B. Claude Code·Codex 마켓플레이스 설치

아래 명령은 GitHub의 이 저장소에서 플러그인을 설치합니다. Claude나 OpenAI의 공식 앱
스토어에서 설치하는 방식은 아닙니다. 앞 단계에서 프로그램 설치와 러너포커 로그인을
마쳤다면, 사용하는 앱에 해당하는 명령만 실행하세요.

Claude Code 대화 안에서:

```text
/plugin marketplace add dadadamarine/runnerpoker-mcp
/plugin install runnerpoker@runnerpoker-community
```

Codex를 사용하는 터미널에서:

```bash
codex plugin marketplace add dadadamarine/runnerpoker-mcp
codex plugin add runnerpoker@runnerpoker-community
```

설치 후 새 세션을 시작합니다. `plugin` 명령을 찾지 못하면 설치된 클라이언트 버전의
플러그인 지원을 확인하거나 아래 MCP 직접 추가 방식을 사용하세요.
플러그인은 uv의 `uvx`로 고정된 서버 소스 버전을 받아 실행하며, 첫 실행에는 네트워크가
필요합니다. 러너포커 인증은 3단계에서 저장한 로컬 파일을 공유합니다.

플러그인 없이 직접 추가하려면 설치 폴더에서 다음 중 하나를 실행합니다.
두 방식을 동시에 설정하면 같은 도구가 중복으로 표시될 수 있으므로 한 가지를 선택하세요.

```bash
# Claude Code만 사용하는 경우
claude mcp add --scope user runnerpoker -- uv run --frozen --directory "$PWD" runnerpoker-mcp
```

```bash
# Codex만 사용하는 경우
codex mcp add runnerpoker -- uv run --frozen --directory "$PWD" runnerpoker-mcp
```

### 4-C. ChatGPT 데스크톱 앱

현재 패키지는 **로컬 실행 플러그인**입니다. ChatGPT 앱 내 실제 도구 사용은 아직
검증되지 않았으므로, Codex에서 설치됐다는 이유만으로 ChatGPT에서도 연결됐다고
판단하지 마세요.

로컬 마켓플레이스를 지원하는 데스크톱 환경에서는 다음 순서로 시도합니다.

1. 1~3단계의 소스 설치와 계정 연결을 완료합니다.
2. 개인 카탈로그 `~/.agents/plugins/marketplace.json`에 아래 항목을 추가합니다.
   파일이 이미 있다면 기존 이름·설정을 바꾸지 말고 `plugins` 배열에 항목만 합칩니다.
   아래는 **기존 파일이 없을 때**의 전체 예시입니다.

```json
{
  "name": "runnerpoker-desktop",
  "interface": {"displayName": "RunnerPoker Desktop"},
  "plugins": [
    {
      "name": "runnerpoker",
      "source": {"source": "local", "path": "./Applications/runnerpoker-mcp"},
      "policy": {"installation": "AVAILABLE", "authentication": "ON_USE"},
      "category": "Productivity"
    }
  ]
}
```

3. `source.path`는 이 개인 카탈로그의 루트인 홈 폴더 기준입니다. 2단계와 다른 곳에
   설치했다면 실제 경로로 조정합니다. 상대 경로는 `./`로 시작하며 홈 폴더 안에 둡니다.
4. 앱을 다시 열고 플러그인 디렉터리의 **RunnerPoker Desktop** 소스에서
   **RunnerPoker**를 찾아 설치합니다. 이전에 다른 소스로 설치했다면 중복 설치하지 않습니다.
5. 로컬 실행 대화에서 아래 첫 조회를 확인합니다. **메뉴가 없거나 도구가 나타나지 않으면
   연결 성공으로 처리하지 않습니다.** 앱 버전·계정·실행 모드의 지원 여부를 확인해야 합니다.

이 저장소의 `.agents/plugins/marketplace.json`은 프로젝트 단위 카탈로그이고,
루트 `plugin.json`과 `mcp.json`이 로컬 실행 설정입니다. 지원되는 소스를 사용해 설치하는
방식이며, 개인 카탈로그를 넣는 것만으로 모든 ChatGPT 앱에서 사용 가능해지는 것은 아닙니다.

일반 웹 커넥터의 URL 입력란에 로컬 폴더나 `api.runnerpoker.com`을 입력하는 방식은
지원하지 않습니다. 이 서버는 공개 HTTPS MCP 주소를 제공하지 않습니다.
공식 공개 디렉터리 배포에는 별도 조건이 있습니다.
[OpenAI 로컬 MCP 배포 안내](https://developers.openai.com/plugins/deploy/desktop-only).

### 5. 첫 조회와 연결 확인

연결한 앱의 새 대화에 다음 문장을 입력합니다.

> 러너포커 MCP의 auth_status를 확인하고, get_timeline으로 최근 7일 중
> 첫 페이지 1개를 실제 조회해줘. 연결 성공 여부만 알려줘.

**성공 기준은 두 가지입니다.**

- `auth_status`에서 `configured: true`가 나옵니다.
- 실제 조회가 인증 오류 없이 성공하고 타임라인 데이터가 반환됩니다. 기록이 없어도 빈 결과는 정상일 수 있습니다.

`auth_status`의 `remote_session_verified: false`는 항상 반환되는 값입니다.
이 도구는 로컬 파일만 확인하므로 이 값만 보고 세션 만료라고 판단하지 마세요.
반대로 `configured: true`만으로 계정 연결이 유효하다고 판단해서도 안 됩니다.

### 6. 이렇게 물어보세요

| 하고 싶은 일 | 복사해서 사용할 요청 |
|---|---|
| 오늘 기록 확인 | 오늘 플레이 요약과 세션 목록을 보여줘. |
| 기간 지정 | 2026년 11월 1일부터 7일까지 홀덤 요약을 보여줘. |
| 파켓페어 비교 | 최근 7일 AA부터 22까지 손익과 핸드 수를 보여줘. 실제 조회 범위와 표본 부족도 표시해줘. |
| 한 세션 복기 | 최근 마스터 세션 하나를 찾아서, 그 세션의 파켓페어 손익을 비교해줘. |
| 손실 복기 | 그 세션에서 50BB 이상 잃은 파켓페어 핸드 3개를 찾아 당시 정보만으로 리뷰해줘. |
| 결과 편향 줄이기 | 같은 조건에서 이긴 핸드도 같이 비교해줘. 진 결과만으로 실수라고 판단하지 마. |

`BB`는 빅블라인드 단위이고 `BB/100`은 100핸드당 비율입니다. 손익 금액과 서로 다른
지표입니다. AA는 에이스 두 장, `AKs`는 같은 무늬 AK, `AKo`는 다른 무늬 AK입니다.
HUD는 VPIP·PFR 같은 플레이 성향 통계입니다. 레인지 분석은 기록 분류이며 솔버 해답이 아닙니다.

루키·마스터, 2인·6인, 서로 다른 스택 깊이를 한데 섞으면 전략 해석이 달라질 수 있습니다.
세션을 먼저 골라 분석하면 비교 조건을 맞추기 쉽습니다. 핸드 레인지·스팟 집계 도구는
채널 필터를 직접 받지 않으므로, 채널을 구분하려면 세션 목록에서 해당 채널을 찾고
`session_id`로 조회합니다. AI가 적용하지 않은 필터를 적용했다고 말하면 안 됩니다.

기본 조회 예산은 전체 기록보다 작을 수 있습니다. “전체 분석”을 원하면 AI에게
`history_exhausted`와 실제 조회 건수를 확인하도록 요청하세요. 패배 기록만으로는
전략의 수익성을 판단할 수 없고, 작은 표본의 손익은 장기 실력을 뜻하지 않습니다.

### 7. 연결이 안 될 때

| 증상 | 확인할 것과 해결 방법 |
|---|---|
| `command not found: uv` 또는 `uvx` | uv 설치 후 터미널을 새로 열고 버전을 확인합니다. 앱 설정에는 실행 파일 전체 경로를 사용합니다. |
| 설치 폴더가 이미 있다고 나옴 | 기존 설치 폴더로 이동합니다. 내용을 확인하지 않고 폴더를 지우지 마세요. |
| 앱에 도구가 안 보임 | 해당 앱용으로 설정했는지 확인합니다. Claude Code 설정과 Claude 앱 설정은 다릅니다. 앱을 완전히 재시작합니다. |
| `configured: false` | 3단계 인증을 진행합니다. 다른 OS 사용자나 다른 컴퓨터의 인증 파일은 자동 공유되지 않습니다. |
| `Session expired or access denied` | 오류 메시지의 [Craft 링크](https://craft.runnerpoker.com/ko/holdem/summary)에서 다시 로그인한 뒤 3단계로 인증 파일을 갱신합니다. 401/403은 접근 거부일 수도 있습니다. |
| `Could not save credentials` | accessToken이 전체 값인지, userSeq가 양의 정수인지 확인합니다. 쿠키를 토큰 대신 넣지 않습니다. |
| 기록이 비어 있음 | 기간·계정·채널·세션 조건을 확인합니다. 빈 결과를 연결 실패나 손익 0으로 단정하지 않습니다. |
| 전체 기록이 아닌 것 같음 | 페이지·상세 조회 예산과 `coverage`를 확인하고 날짜나 세션을 좁힙니다. |
| 손익이 매우 큰 BB로 나옴 | 원본 손익과 그 핸드의 BB, 채널·스택을 대조합니다. 큰 값만으로 오류라고 하거나 임의 제외하지 않습니다. |
| 요청 제한·429 | 잠시 후 범위를 줄여 다시 조회합니다. 반복 호출하지 않습니다. |
| 터미널에서 서버를 켰는데 아무 출력이 없음 | stdio 서버가 앱의 요청을 기다리는 정상 상태일 수 있습니다. 직접 켜두지 말고 앱 설정을 통해 실행합니다. |
| ChatGPT 앱에 로컬 플러그인 메뉴가 없음 | 현재 앱 환경에서 지원되는지 확인합니다. Claude 앱이나 Codex에서 성공했다는 사실로 대체하지 않습니다. |

인증 파일 갱신은 서버가 요청마다 다시 읽으므로 보통 서버 재시작이 필요 없습니다.
앱의 **실행 설정**을 바꿨다면 앱 또는 MCP 연결을 재시작해야 합니다.
프로젝트를 소스로 설치한 경우 업데이트는 설치 폴더에서 `git pull --ff-only` 후
`uv sync --frozen`으로 진행합니다. 마켓플레이스 패키지는 고정된 서버 버전을 사용하므로
소스 폴더를 업데이트하는 것과 플러그인 업데이트는 별개입니다.

## 마켓플레이스와 ChatGPT 배포 상태

이 저장소의 마켓플레이스는 저장소 주소로 추가하는 커뮤니티 배포 경로입니다.
공식 Claude·ChatGPT·Codex 디렉터리 등재나 러너포커의 공식 승인을 의미하지 않습니다.

- Claude Code: `.claude-plugin/marketplace.json`과 `.claude-plugin/plugin.json`
- Codex 및 지원되는 로컬 데스크톱 환경: `.agents/plugins/marketplace.json`, `plugin.json`, `mcp.json`
- 기존 Codex 형식 호환: `.codex-plugin/plugin.json`, `.mcp.json`
- Claude 앱: 위 4-A의 로컬 MCP 설정. Code용 마켓과는 별도입니다.

공식 제출은 아직 하지 않았습니다. OpenAI의 로컬 MCP 공식 등재는 승인된 파트너와
제출 조직 허용 등록이 필요하며, ChatGPT·Codex 공개 디렉터리는 공유됩니다.
Claude 앱의 로컬 확장 디렉터리는 Code용 저장소 마켓과 다른 제출 경로입니다.
제출 절차와 현재 남은 조건은 [배포 안내](docs/DISTRIBUTION.md)를 참고하세요.

아래부터는 도구 인자와 구현을 확인하려는 분을 위한 상세 설명입니다.

## 도구

| 도구 | 기능 |
|---|---|
| `auth_status` | 로컬 인증 파일의 설정 여부 확인. 원격 세션 유효성은 검사하지 않음 |
| `get_timeline` | 기간별 타임라인 한 페이지와 서버 제공 성과 정보 조회 |
| `get_timeline_day` | `YYYY-MM-DD` 날짜의 상세 이벤트 조회 |
| `list_hand_histories` | 세션·날짜별 핸드 목록, 커서 기반 다음 페이지 조회 |
| `get_hand_history` | 특정 핸드의 v2 원본 기록(플레이어·보드·액션·사이징·팟) |
| `search_review_hands` | 파켓페어·3벳 팟·리버 참여·수익/손실 조건 검색과 리뷰 기록 수집 |
| `get_holdem_summary` | 홀덤 요약과 같은 기간·채널의 HUD (VPIP, PFR, 3Bet 등) |
| `get_position_stats` | 기간·채널·포지션별 통계 (핸드, BB/100, EV BB/100 등 원본 지표) |
| `get_hud_stats` | 기간별 또는 특정 세션의 HUD |
| `list_holdem_sessions` | 기간별 세션 목록, 시작일시 최신순 |
| `get_session_performance` | 세션 성과와 서버에서 제공하는 스택 추세 |
| `get_hand_histories` | 1–30개 핸드의 실제 v2 기록 일괄 조회, 부분 실패 명시 |
| `get_hand_range_stats` | 핸드 레인지 분석: AA·AKs·AKo 등 클래스별 손익·핸드 수 |
| `summarize_review_spots` | 포지션·핸드 클래스·팟 유형·리버 참여별 리뷰 표본 집계 |

`get_timeline` 인자: `period` (`all`, `today`, `thisWeek`, `thisMonth`, `custom`),
`start_date`, `end_date`, `page` (기본 1), `page_size` (기본 10, 최대 100).
`custom`은 시작·종료 날짜가 모두 필요합니다. `thisWeek`은 한국 시간 기준 오늘 포함
최근 7일을 `custom`으로 변환합니다. 나머지 preset은 서버가 해석합니다.
자동 전체 페이지 수집은 하지 않습니다. 응답은 원본 JSON 그대로 반환합니다.

### 핸드 검색 → LLM 리뷰

다음과 같이 요청하면 LLM이 `search_review_hands` 인자로 변환할 수 있습니다.

- “세션 123456에서 파켓페어로 플레이한 3벳 팟 손실 핸드 찾아서 리뷰해줘.”
- “최근 기록 중 리버까지 간 핸드에서 50BB 이상 잃은 것을 찾아줘.”
- “이번 달 크게 이긴 핸드를 살펴보고 결과와 별개로 내 판단을 리뷰해줘.”

첫 번째 요청의 도구 호출 예시:

```json
{
  "session_id": 123456,
  "pocket_pairs_only": true,
  "pot_type": "three_bet",
  "result": "lost",
  "sort": "biggest_loss"
}
```

`/ko/holdem/record/{번호}`의 번호는 API `ParticipantId`에 대응합니다.
위 `123456`은 설명용 가상 번호이며 본인의 세션 번호로 바꿔야 합니다.
`list_hand_histories`는 `game_type`, `session_id`, `start_date`, `end_date`, `cursor`,
`page_size`를 받습니다. 날짜는 한국 시간의 해당 날짜 전체를 UTC ISO 시각으로 변환합니다.
`get_hand_history`에는 목록의 `handId`를 `hand_id`로 전달합니다.

검색 조건은 다음과 같습니다. 자연어 해석은 MCP 클라이언트의 LLM이 담당합니다.

| 인자 | 의미 |
|---|---|
| `pocket_pairs_only` | 알려진 홀카드가 AA–22인 핸드 |
| `pot_type="three_bet"` | 프리플롭에서 오픈과 재레이즈가 발생하고 4벳은 없는 팟 |
| `reached_river=true` | Hero가 리버 전 폴드하지 않고 리버까지 참여한 핸드 |
| `result` | `any`, `won`, `lost` (실현 손익 기준) |
| `min_abs_net_bb` | 캐시게임 손익 절댓값의 BB 기준 하한 |
| `sort` | `recent`, `biggest_loss`, `biggest_win`, `largest_swing` |
| `max_pages` | 조회 페이지 예산: 기본 3, 최대 20 (페이지당 100핸드) |
| `max_details` | 상세 조회 예산: 기본 30, 최대 100 |
| `limit` | 반환할 리뷰 핸드 수: 기본 20, 최대 100 |

서버에서 지원하는 것으로 확인되지 않은 스팟 필터는 로컬에서 판정합니다.
**예산 내에 확인한 표본**에서 정렬하며 전체 이력 최악/최선 핸드라고 보장하지 않습니다.
`history_exhausted`, `classification_complete`, `stop_reason`, `unclassified_count`,
`results_truncated`를 확인해야 합니다. `recent`는 상류 목록 순서를 유지하며 최신순이라는
실제 서버 보장은 아직 검증하지 않았습니다. 필요하면 날짜나 세션을 좁혀 다시 조회하세요.

카드 ID는 웹앱의 1–52 인코딩을 따릅니다. 알 수 없는 카드, 불충분한 액션,
스트래들·숏 올인 등 애매한 팟 구조는 추측하지 않고 미판정으로 처리합니다.
리버 참여에는 앞 스트리트 올인 후 런아웃도 포함될 수 있습니다.
`hero_has_river_action`으로 리버 액션 유무를 별도로 확인하세요.
금전 손실은 전략적 실수나 EV 손실의 증거가 아니며, 이 서버는 솔버를 실행하지 않습니다.
토너먼트에 캐시 BB 수익 지표를 적용하지 않습니다.

### 로직으로 판정하는 조건

분류와 계산은 Python 코드가 수행하며 LLM 호출을 사용하지 않습니다.

| 조건 | 판정 근거 |
|---|---|
| 파켓페어·수티드·오프수트 | 1–52 카드 ID의 랭크·수트 |
| 3벳 팟 | BB 포스팅이 있는 프리플랍 기록의 유효 레이즈 2회. 4벳 이상 제외 |
| 리버 참여 | 유효한 5장 보드 + Hero의 명시적 리버 액션 또는 이전 스트리트의 명시적 AllIn |
| 리버 미참여 | 리버 전 Hero Fold 또는 리버 전에 끝난 유효한 최종 보드 |
| 손익·BB/100 | 원본 netDelta와 해당 핸드의 bigBlind로 계산, 누락 값은 제외·표시 |

보드 5장과 타인의 액션만으로 Hero가 리버에 참여했다고 판정하지 않습니다.
Hero의 턴 Check도 이후 폴드 여부를 알 수 없으면 리버 참여 증거가 되지 않습니다.
폴드·올인 이후 Hero 추가 액션처럼 서로 모순되는 기록, 잘못된 카드·중복 액션 순번은
미확인으로 남깁니다. `spot.reasons`에 판정/미판정 사유 코드를 반환합니다.
기록의 완전성을 API가 보장하는지 아직 실계정으로 확인하지 않았으므로 분류 결과는
관측한 데이터에 대한 판정입니다. 임의로 누락 액션을 복원하지 않습니다.

집계의 `coverage`는 다음 상태를 독립 표시합니다.

- `history_exhausted`: 서버의 마지막 페이지까지 조회했는지
- `classification_complete`: 검색 필터와 반환 표본의 집계 축에 미확인이 없는지
- `profit_complete`: 반환 표본에 BB 손익 누락이 없는지 (필터 미확인·결과 잘림도 보수적으로 반영)
- `analysis_complete`: 전체 이력 조회·분류·손익 데이터가 모두 완료됐는지
- `filter_unknown_count`, `group_unknown_count`, `missing_bb_results_count`: 각 미확인·누락 건수

일부 페이지의 핸드를 모두 분류했어도 `history_exhausted=false`면 전체 분석 완료가 아닙니다.
LLM은 미확인 값을 재추측하지 않고, 전략 리뷰에서도 해당 액션 당시 알 수 있었던 정보만
사용해야 합니다. 이후 보드·쇼다운 결과는 의사결정 평가와 별도로 다룹니다.

### 홀덤 요약·포지션·핸드 레인지 분석

- “이번 달 홀덤 요약에서 VPIP, PFR, 3Bet 보여줘.”
  → `get_holdem_summary(period="thisMonth")`
- “최근 7일 BB 포지션 성적 보여줘.”
  → `get_position_stats(period="thisWeek", selected_positions=["BB"])`
- “11월 1일부터 7일까지 BTN과 CO 비교해줘.”
  → `get_position_stats(period="custom", start_date="2026-11-01", end_date="2026-11-07",
  selected_positions=["BTN", "CO"])`
- “AA와 KK의 손익을 보고 실제 핸드 리뷰해줘.”
  → `get_hand_range_stats(selected_hands=["AA", "KK"], start_date=..., end_date=...)`
  → 반환된 `matching_hand_ids`로 `get_hand_histories(hand_ids=[...])`
- “파켓페어 3벳 팟에서 어느 포지션 손익이 나쁜지 비교해줘.”
  → `summarize_review_spots(group_by="position", pocket_pairs_only=true, pot_type="three_bet")`

통계 도구는 사이트의 용어를 사용합니다. `runnerpoker://terminology` 리소스에 원본 필드와
`VPIP`, `PFR`, `3Bet`, `플랍 C-bet`, `WTSD`, `WSD`, `손익`, `BB/100`, `EV BB/100`
표기 대응을 제공합니다. HUD 원본 비율은 그대로 반환하며 사이트는 0–1 값을 퍼센트로
표시합니다. 두 번 변환하지 마세요. 기회 수와 분모는 서버 값을 유지합니다.

포지션 통계의 `BB/100`은 비율이며 총손익이 아닙니다. 서버가 제공하지 않는 총손익을
반올림된 비율에서 만들어내지 않습니다. `EV BB/100`도 원본 지표로 취급하며 솔버의 EV
판정이라고 부르지 않습니다. `channel_ids`를 생략하면 명시적 채널 필터를 보내지 않으므로,
사이트에서 선택한 채널과 다르면 결과가 달라질 수 있습니다.

`get_hand_range_stats`는 사이트의 핸드 레인지 분석처럼 **목록만** 읽어 캐시 핸드를
169개 클래스로 묶습니다. 상세 액션을 받지 않아 기간별 클래스 손익 조회에 적합합니다.
`max_pages` 기본 3·최대 20, 페이지당 100핸드이며, 일부만 읽으면 `coverage`에 표시합니다.
`selected_hands`에는 `AA`, `AKs`, `AKo`처럼 표준 클래스명을 넣습니다. 선택한 클래스가
표본에서 관측되지 않으면 `unobserved_hands`에 표시하며 손익 0으로 만들지 않습니다.

`summarize_review_spots`는 승리·패배 핸드를 모두 포함해 조건에 맞는 **리뷰 표본**을
집계합니다. `group_by`는 `position`, `hand_class`, `pot_type`, `river_participation`입니다.
`net_bb`는 표본의 BB 단위 손익 합계, `sample_bb_per_100`은 그 표본의 BB/100입니다.
`min_samples` 기본 20 미만 그룹도 숨기지 않고 `below_min_samples`(표본 부족)를 표시합니다.
임계값을 넘었다고 통계적으로 충분한 표본임을 보장하지 않습니다.
결과 누락은 분모에서 제외하고 건수를 표시합니다. 미확인 그룹도 유지합니다.
조건부 표본의 BB/100을 전체 핸드의 승률로 설명하지 마세요.

`get_session_performance`의 스택 증가는 리바이를 포함할 수 있으므로 손익 증가와 동일시하지
않습니다. `get_hand_histories`는 성공한 기록과 `errors`를 함께 반환하며 `complete=false`면
요청한 핸드를 전부 받았다고 말하지 않습니다.

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
