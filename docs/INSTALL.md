# 설치와 연결 가이드

[README](../README.md)의 빠른 시작을 단계별로 풀어 쓴 문서입니다.

## 처음 사용하는 분께

### 먼저 사용할 데스크톱 앱을 고르세요

아래에서 쓰는 앱 하나만 고르세요.

- **Claude 데스크톱 앱:** [설치 방법](#4-a-claude-데스크톱-앱-연결하기)
- **Codex 데스크톱 앱:** [설치 방법](#4-b-claude-codecodex-마켓플레이스-설치)의 Codex 안내
- **Claude Code:** [설치 방법](#4-b-claude-codecodex-마켓플레이스-설치)의 Claude Code 안내
- **ChatGPT 데스크톱 앱:** [설치 방법](#4-c-chatgpt-데스크톱-앱). 앱에 플러그인 메뉴가 있어야 합니다.

웹브라우저에서 여는 ChatGPT와 Claude에는 연결할 수 없습니다.

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
“이 저장소 docs/INSTALL.md의 절차대로 RunnerPoker를 설치하고, 중간에 필요한 화면을
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
> 설치 폴더 docs/DEVELOPMENT.md의 로컬 Chrome 인증 추출 절차로 해당 사이트의 accessToken과 userSeq만 읽고,
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

먼저 [프로그램 설치](#2-프로그램-받기)와 [러너포커 로그인](#3-러너포커-계정-연결하기)을
마치세요. 그다음 사용하는 앱에 맞는 명령 하나만 실행합니다. 이 설치 방법은 앱의 공식
스토어가 아니라 GitHub에서 플러그인을 가져옵니다.

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

복사해서 쓸 수 있는 예시 요청은 [README의 이렇게 물어보세요](../README.md#이렇게-물어보세요)에
있습니다. 아래는 결과를 읽을 때 알아둘 점입니다.

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
제출 절차와 현재 남은 조건은 [배포 안내](DISTRIBUTION.md)를 참고하세요.

