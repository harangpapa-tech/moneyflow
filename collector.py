"""
머니플로우 — 한국투자증권 API 데이터 수집기
매일 자동으로 실행되어 외국인/기관 수급 데이터를 수집합니다
"""

import requests
import json
import datetime
import os

# ── API 설정 ──────────────────────────────
APP_KEY = os.environ.get('KIS_APP_KEY', '')
APP_SECRET = os.environ.get('KIS_APP_SECRET', '')
BASE_URL = 'https://openapi.koreainvestment.com:9443'

# ── 섹터 매핑 ─────────────────────────────
SECTOR_MAP = {
    '005930': '반도체', '000660': '반도체', '042700': '반도체',
    '373220': '2차전지', '006400': '2차전지', '247540': '2차전지',
    '012450': '방산', '047810': '방산', '034020': '원전',
    '009540': '조선', '010140': '조선', '042660': '조선',
    '207940': '바이오', '068270': '바이오', '326030': '바이오',
    '105560': '금융', '055550': '금융', '086790': '금융',
    '005380': '자동차', '000270': '자동차',
    '035420': 'IT', '035720': 'IT', '251270': 'IT',
}

def get_today():
    return datetime.date.today().strftime('%Y%m%d')

def get_display_date():
    return datetime.date.today().strftime('%Y.%m.%d')

# ── 1. 액세스 토큰 발급 ────────────────────
def get_access_token():
    print("🔑 토큰 발급 중...")
    url = f"{BASE_URL}/oauth2/tokenP"
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET
    }
    res = requests.post(url, json=body)
    token = res.json().get('access_token', '')
    if token:
        print("  ✅ 토큰 발급 성공")
    else:
        print("  ❌ 토큰 발급 실패:", res.json())
    return token

# ── 2. 외국인 순매수 TOP ───────────────────
def get_foreign_top(token):
    print("📡 외국인 순매수 수집 중...")
    url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/volume-rank"
    headers = {
        'content-type': 'application/json',
        'authorization': f'Bearer {token}',
        'appkey': APP_KEY,
        'appsecret': APP_SECRET,
        'tr_id': 'FHPST01710000',
        'custtype': 'P'
    }
    params = {
        'FID_COND_MRKT_DIV_CODE': 'J',
        'FID_COND_SCR_DIV_CODE': '20171',
        'FID_INPUT_ISCD': '0000',
        'FID_DIV_CLS_CODE': '0',
        'FID_BLNG_CLS_CODE': '0',
        'FID_TRGT_CLS_CODE': '111111111',
        'FID_TRGT_EXLS_CLS_CODE': '000000',
        'FID_INPUT_PRICE_1': '',
        'FID_INPUT_PRICE_2': '',
        'FID_VOL_CNT': '',
        'FID_INPUT_DATE_1': ''
    }

    try:
        # 외국인 순매수 상위 종목
        url2 = f"{BASE_URL}/uapi/domestic-stock/v1/ranking/investor"
        headers2 = {
            'content-type': 'application/json',
            'authorization': f'Bearer {token}',
            'appkey': APP_KEY,
            'appsecret': APP_SECRET,
            'tr_id': 'FHPST02320000',
            'custtype': 'P'
        }
        params2 = {
            'FID_COND_MRKT_DIV_CODE': 'J',
            'FID_COND_SCR_DIV_CODE': '20232',
            'FID_INPUT_ISCD': '0001',
            'FID_DIV_CLS_CODE': '0',
            'FID_BLNG_CLS_CODE': '1',  # 1: 외국인
            'FID_TRGT_CLS_CODE': '111111111',
            'FID_TRGT_EXLS_CLS_CODE': '000000',
            'FID_INPUT_PRICE_1': '',
            'FID_INPUT_PRICE_2': '',
            'FID_VOL_CNT': '10',
            'FID_INPUT_DATE_1': get_today()
        }
        res = requests.get(url2, headers=headers2, params=params2)
        data = res.json()
        output = data.get('output', [])

        stocks = []
        for i, item in enumerate(output[:10]):
            name = item.get('hts_kor_isnm', '')
            code = item.get('mksc_shrn_iscd', '')
            price = item.get('stck_prpr', '0')
            change_rate = item.get('prdy_ctrt', '0')
            net_buy = item.get('frgn_ntby_qty', '0')

            try:
                net_buy_int = int(net_buy)
                net_buy_str = f"+{net_buy_int:,}" if net_buy_int > 0 else f"{net_buy_int:,}"
            except:
                net_buy_str = net_buy

            stocks.append({
                'name': name,
                'code': code,
                'sector': SECTOR_MAP.get(code, '기타'),
                'price': f"{int(price):,}원" if price.isdigit() else price,
                'change': f"+{change_rate}%" if not change_rate.startswith('-') else f"{change_rate}%",
                'netBuy': net_buy_str + '주',
                'ratio': max(10, 100 - i * 9),
            })

        print(f"  ✅ 외국인 {len(stocks)}종목 수집 완료")
        return stocks

    except Exception as e:
        print(f"  ⚠️ 외국인 수집 실패: {e}")
        return []

# ── 3. 기관 순매수 TOP ─────────────────────
def get_inst_top(token):
    print("📡 기관 순매수 수집 중...")
    try:
        url = f"{BASE_URL}/uapi/domestic-stock/v1/ranking/investor"
        headers = {
            'content-type': 'application/json',
            'authorization': f'Bearer {token}',
            'appkey': APP_KEY,
            'appsecret': APP_SECRET,
            'tr_id': 'FHPST02320000',
            'custtype': 'P'
        }
        params = {
            'FID_COND_MRKT_DIV_CODE': 'J',
            'FID_COND_SCR_DIV_CODE': '20232',
            'FID_INPUT_ISCD': '0001',
            'FID_DIV_CLS_CODE': '0',
            'FID_BLNG_CLS_CODE': '2',  # 2: 기관
            'FID_TRGT_CLS_CODE': '111111111',
            'FID_TRGT_EXLS_CLS_CODE': '000000',
            'FID_INPUT_PRICE_1': '',
            'FID_INPUT_PRICE_2': '',
            'FID_VOL_CNT': '10',
            'FID_INPUT_DATE_1': get_today()
        }
        res = requests.get(url, headers=headers, params=params)
        data = res.json()
        output = data.get('output', [])

        stocks = []
        for i, item in enumerate(output[:10]):
            name = item.get('hts_kor_isnm', '')
            code = item.get('mksc_shrn_iscd', '')
            price = item.get('stck_prpr', '0')
            change_rate = item.get('prdy_ctrt', '0')
            net_buy = item.get('orgn_ntby_qty', '0')

            try:
                net_buy_int = int(net_buy)
                net_buy_str = f"+{net_buy_int:,}" if net_buy_int > 0 else f"{net_buy_int:,}"
            except:
                net_buy_str = net_buy

            stocks.append({
                'name': name,
                'code': code,
                'sector': SECTOR_MAP.get(code, '기타'),
                'price': f"{int(price):,}원" if price.isdigit() else price,
                'change': f"+{change_rate}%" if not change_rate.startswith('-') else f"{change_rate}%",
                'netBuy': net_buy_str + '주',
                'ratio': max(10, 100 - i * 9),
            })

        print(f"  ✅ 기관 {len(stocks)}종목 수집 완료")
        return stocks

    except Exception as e:
        print(f"  ⚠️ 기관 수집 실패: {e}")
        return []

# ── 4. 코스피 지수 ─────────────────────────
def get_kospi(token):
    print("📡 코스피 지수 수집 중...")
    try:
        url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-index-price"
        headers = {
            'content-type': 'application/json',
            'authorization': f'Bearer {token}',
            'appkey': APP_KEY,
            'appsecret': APP_SECRET,
            'tr_id': 'FHPUP02100000',
            'custtype': 'P'
        }
        params = {'FID_COND_MRKT_DIV_CODE': 'U', 'FID_INPUT_ISCD': '0001'}
        res = requests.get(url, headers=headers, params=params)
        data = res.json().get('output', {})

        value = data.get('bstp_nmix_prpr', 'N/A')
        change = data.get('bstp_nmix_prdy_ctrt', 'N/A')

        try:
            v = float(value)
            value = f"{v:,.2f}"
        except:
            pass

        print(f"  ✅ KOSPI: {value}")
        return {
            'value': value,
            'change': f"+{change}%" if change and not change.startswith('-') else f"{change}%",
            'isUp': not str(change).startswith('-')
        }
    except Exception as e:
        print(f"  ⚠️ 코스피 수집 실패: {e}")
        return {'value': 'N/A', 'change': 'N/A', 'isUp': True}

# ── 5. 섹터별 수급 집계 ────────────────────
def calc_sectors(foreign_top, inst_top):
    sector_data = {}

    for s in foreign_top:
        sec = s['sector']
        if sec not in sector_data:
            sector_data[sec] = {'foreign': 0, 'inst': 0}
        sector_data[sec]['foreign'] += 1

    for s in inst_top:
        sec = s['sector']
        if sec not in sector_data:
            sector_data[sec] = {'foreign': 0, 'inst': 0}
        sector_data[sec]['inst'] += 1

    result = []
    for name, vals in sector_data.items():
        result.append({
            'name': name,
            'foreign': vals['foreign'] * 800,
            'inst': vals['inst'] * 600,
        })

    result.sort(key=lambda x: x['foreign'] + x['inst'], reverse=True)
    return result[:8]

# ── 6. 5일 추이 데이터 ─────────────────────
def update_history(existing_data, kospi, foreign_total, inst_total):
    history = existing_data.get('history', [])
    today = get_display_date()

    # 오늘 데이터가 이미 있으면 업데이트
    today_exists = any(h['date'] == today for h in history)
    if not today_exists:
        history.append({
            'date': today,
            'foreign': foreign_total,
            'inst': inst_total,
        })

    return history[-5:]  # 최근 5일만

# ── 메인 ───────────────────────────────────
def main():
    print("=" * 45)
    print("  머니플로우 데이터 수집 시작")
    print(f"  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 45)

    if not APP_KEY or not APP_SECRET:
        print("❌ API 키가 없습니다. GitHub Secrets 확인하세요.")
        return

    # 토큰 발급
    token = get_access_token()
    if not token:
        print("❌ 토큰 발급 실패. 종료합니다.")
        return

    # 데이터 수집
    kospi = get_kospi(token)
    foreign_top = get_foreign_top(token)
    inst_top = get_inst_top(token)
    sectors = calc_sectors(foreign_top, inst_top)

    # 기존 데이터 불러오기
    existing = {}
    if os.path.exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as f:
            existing = json.load(f)

    # 수급 합계 (간단 추정)
    foreign_total = len(foreign_top) * 300
    inst_total = -len(inst_top) * 200

    history = update_history(existing, kospi, foreign_total, inst_total)

    # 최종 데이터
    data = {
        'date': get_display_date(),
        'updated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'kospi': kospi,
        'foreign_top': foreign_top,
        'inst_top': inst_top,
        'sectors': sectors,
        'foreign_total': foreign_total,
        'inst_total': inst_total,
        'history': history,
    }

    # 저장
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 완료! data.json 저장됨")
    print(f"   외국인 TOP: {len(foreign_top)}종목")
    print(f"   기관 TOP: {len(inst_top)}종목")
    print(f"   섹터: {len(sectors)}개")

if __name__ == '__main__':
    main()
