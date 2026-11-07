# 배포 경로와 검증 상태

## 현재 제공하는 패키지

| 대상 | 제공하는 것 | 아직 확인하지 않은 것 |
|---|---|---|
| Claude 앱 | README의 로컬 stdio 실행 설정. 앱 UI에서 실행 상태와 실제 조회 확인 | 다른 사용자·OS의 설치 흐름 |
| Claude Code | `.claude-plugin/` 카탈로그·manifest, `.mcp.json` | 새 사용자 계정의 설치 흐름 |
| Codex | `.agents/plugins/` 카탈로그, portable/호환 manifest | 다른 OS의 설치 흐름 |
| ChatGPT 데스크톱 | 로컬 실행을 요구하는 portable 패키지 | 앱 내 설치·도구 사용, 공식 디렉터리 승인 |

로컬 검증에서는 Claude 앱에 설정한 명령과 설치된 플러그인 명령을 각각 별도 stdio
클라이언트에서 실행해 initialize → 14개 도구 목록 → 인증 상태 → 실제 타임라인 조회를
확인했습니다. 추가로 Claude 앱을 재시작한 뒤 개발자 설정의 `runnerpoker: 실행 중`과
일반 채팅에서 `auth_status`, `get_timeline` 호출 성공을 확인했습니다.
ChatGPT 앱의 도구 호출까지 검증한 것은 아닙니다.

## 저장소 마켓플레이스

마켓 이름은 `runnerpoker-community`, 플러그인 이름은 `runnerpoker`입니다.
공식 디렉터리에 제출하지 않고도 저장소를 소스로 추가할 수 있는 배포 형식입니다.
앱마다 지원하는 마켓플레이스와 실행 환경이 다르므로 README의 앱별 절차를 따릅니다.

서버 실행은 공개 저장소의 커밋 `eb46c5b34efe7e6368f129c1a9d68cf5bda2e713`에
고정되어 있습니다. 플러그인 설치본에 개인별 설치 경로를 넣지 않기 위해 `uvx`를 사용합니다.
Git·uv와 첫 실행 네트워크가 필요하며, Python 3.11은 uv가 준비합니다.
서버 소스를 고정한 것이며 의존성까지 잠금 파일로 고정하는 `uv sync --frozen`과는 다릅니다.

### 릴리스할 때

1. 서버 변경을 먼저 원격 저장소에 반영하고 검증할 커밋을 결정합니다.
2. `mcp.json`과 `.mcp.json`의 Git 커밋을 함께 갱신합니다.
3. 루트·Claude·Codex manifest의 버전을 함께 올립니다. 서버 버전과 다른 버전을
   쓸 경우 그 이유를 명시합니다.
4. Claude manifest 검증, 패키지 일관성 테스트와 실제 stdio 연결을 실행합니다.
5. 마켓플레이스에서 설치한 캐시 사본도 최신 버전인지 확인합니다.

## Claude 앱의 로컬 확장 디렉터리

Claude Code 플러그인과 Claude 앱의 데스크톱 확장 파일은 같은 형식이 아닙니다.
현재는 Claude 앱 설정 파일에 로컬 MCP를 연결하며 `.mcpb` 확장 파일은 제공하지 않습니다.
원클릭 확장으로 배포하려면 MCPB manifest와 실행 환경을 패키징하고 새 설치를 검증한 뒤
별도 데스크톱 확장 제출 경로를 사용해야 합니다.

공식 안내: [Claude 데스크톱 로컬 MCP와 확장](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop),
[MCPB](https://github.com/anthropics/mcpb).

## ChatGPT·Codex 공식 공개 디렉터리

공식 공개 디렉터리는 공유되지만 저장소 마켓플레이스 등록은 공식 제출이 아닙니다.
이 프로젝트는 로컬 stdio 서버이므로 데스크톱 전용 제출 경로가 대상입니다.
현재 공식 문서상 로컬 MCP 제출은 승인된 파트너로 제한되며 제출 조직의 허용 등록이
선행되어야 합니다. 자격을 확인하지 않은 상태에서 제출 완료·등재 완료라고 하지 않습니다.

공식 제출 전 남은 항목:

- OpenAI 담당자를 통한 로컬 MCP 제출 자격·조직 허용 등록 확인
- 제출 주체의 계정 권한·개발자 신원 확인
- ChatGPT 데스크톱에서 새 설치 및 주요 조회 흐름 검증
- 공식 제출 요구에 맞는 런타임·의존성 포함 패키지 검토
- 실제 운영에 맞는 개인정보 안내·지원 URL·브랜드 자료 준비
- 공식 검증 및 심사, 승인 후 게시

현재 저장소용 패키지를 공식 심사 준비 완료 ZIP으로 표현하지 않습니다.
[데스크톱 전용 제출](https://developers.openai.com/plugins/deploy/desktop-only),
[공개 제출 안내](https://developers.openai.com/plugins/deploy/submission)를 확인하세요.

## 웹 서비스와 인증

공개 HTTPS MCP 서버와 다중 사용자 인증은 구현하지 않았습니다.
로컬 파일의 인증 토큰을 배포 패키지·Git·외부 서버에 포함하지 않습니다.
브라우저 토큰 추출은 공식 OAuth 연동이 아니며, 운영사가 외부 서비스 접근을 허용했다는
근거도 아닙니다. 공개 원격 서비스로 확장하기 전 러너크래프트 운영사의 외부 연동 정책과
공식 인증·API 제공 여부를 먼저 확인해야 합니다.
