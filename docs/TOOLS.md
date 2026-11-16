# 도구 상세

도구 인자와 판정 로직을 확인하려는 분을 위한 문서입니다. 기능 요약은
[README](../README.md#할-수-있는-일)에 있습니다.

## 도구 목록

| 도구 | 기능 |
|---|---|
| `auth_status` | 로컬 인증 파일의 설정 여부 확인. 원격 세션 유효성은 검사하지 않음 |
| `get_timeline` | 기간별 타임라인 한 페이지와 서버 제공 성과 정보 조회 |
| `get_timeline_day` | `YYYY-MM-DD` 날짜의 상세 이벤트 조회 |
| `list_hand_histories` | 세션·날짜별 핸드 목록, 커서 기반 다음 페이지 조회 |
| `get_hand_history` | 특정 핸드의 v2 원본 기록(플레이어·보드·액션·사이징·팟) |
| `get_hand_history_pokerstars` | 핸드를 PokerStars 핸드 히스토리 텍스트로 변환(본인은 `Hero`, 헤더 시각 CET, `bb_units`로 BB 단위 전환)하고 그 텍스트를 내 컴퓨터 클립보드에 복사 |
| `search_review_hands` | 파켓페어·3벳 팟·리버 참여·수익/손실 조건 검색과 리뷰 기록 수집 |
| `get_holdem_summary` | 홀덤 요약과 같은 기간·채널의 HUD (VPIP, PFR, 3Bet 등) |
| `get_position_stats` | 기간·채널·포지션별 통계 (핸드, BB/100, EV BB/100 등 원본 지표) |
| `get_hud_stats` | 기간별 또는 특정 세션의 HUD |
| `list_holdem_sessions` | 기간별 세션 목록, 시작일시 최신순 |
| `get_session_performance` | 세션 성과와 서버에서 제공하는 스택 추세 |
| `get_hand_histories` | 1–30개 핸드의 실제 v2 기록 일괄 조회, 부분 실패 명시 |
| `get_hand_range_stats` | 핸드 레인지 분석: AA·AKs·AKo 등 클래스별 손익·핸드 수 |
| `summarize_review_spots` | 포지션·핸드 클래스·팟 유형·리버 참여별 리뷰 표본 집계 |

`get_hand_history_pokerstars` 인자: `hand_id`, `bb_units` (기본 `false`),
`copy_to_clipboard` (기본 `true`). 응답의 `clipboard.copied`가 복사 성공 여부이고,
`false`일 때는 `clipboard.reason`에 사유가 담깁니다. 클립보드 복사는 macOS에서 동작하며
다른 운영체제에서는 텍스트만 반환합니다. 여러 핸드를 연달아 내보낼 때는
`copy_to_clipboard=false`로 클립보드를 그대로 둘 수 있습니다. 이 복사가 서버가 수행하는
유일한 쓰기이며, 러너포커 계정과 기록은 조회만 합니다.

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

