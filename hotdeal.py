import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
import time

# [1] 데이터 로드 및 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "hotdeal_master_db.csv")
NOTICE_PATH = os.path.join(BASE_DIR, "hotdeal_notice_db.csv")

DISPLAY_COLS = ["플랫폼", "행사일정", "브랜드", "제품명", "정상가", "쿠폰혜택", "카드혜택", "최종혜택가", "사은품"]

def extract_num(val):
    try:
        if pd.isna(val) or val == "" or val is None: return 0.0
        if isinstance(val, (int, float)): return float(val)
        clean_val = "".join(filter(lambda x: x.isdigit() or x == '.', str(val)))
        return float(clean_val) if clean_val else 0.0
    except: return 0.0

def fmt_num(val):
    if val == int(val): return str(int(val))
    return str(val)

@st.cache_data(ttl=1)
def load_data(path):
    if not os.path.exists(path):
        if "master" in path: return pd.DataFrame(columns=["선택", "등록날짜", "카테고리"] + DISPLAY_COLS)
        return pd.DataFrame(columns=["선택", "날짜", "유형", "제목", "내용"])
    df = pd.read_csv(path).fillna("")
    if "선택" not in df.columns: df.insert(0, "선택", False)
    df["선택"] = df["선택"].astype(bool)
    return df

BRAND_DICT = {
    "디지털/가전": ["삼성전자", "LG전자", "애플", "소니", "다이슨", "샤오미", "필립스", "로지텍", "쿠쿠", "쿠첸"],
    "가공식품": ["CJ제일제당", "오뚜기", "농심", "동원F&B", "대상(청정원)", "풀무원", "삼양식품", "팔도", "매일유업", "빙그레"],
    "신선식품": ["하림", "목우촌", "팜스코", "선진포크", "본죽", "한우한돈", "우리수산", "프레시지", "마켓컬리"],
    "건강기능식품": ["정관장", "종근당건강", "뉴트리원", "에스더포뮬러", "고려은단", "세노비스", "안국건강", "락토핏"],
    "생활/리빙": ["유한양행", "피앤지", "LG생활건강", "애경", "깨끗한나라", "한샘", "모던하우스", "다이소", "테팔"],
    "패션/잡화": ["나이키", "아디다스", "뉴발란스", "노스페이스", "구찌", "프라다", "지오다노", "무신사스탠다드", "크록스"],
    "뷰티": ["아모레퍼시픽", "올리브영", "설화수", "닥터자르트", "이니스프리", "랑콤", "에스티로더", "헤라", "넘버즈인"]
}

st.set_page_config(page_title="HOTDEAL STRATEGY HUB", layout="wide")

# [2] 통합 CSS 스타일 (줄바꿈 보존 로직 포함)
st.markdown("""
    <style>
    div[data-testid="stTextInput"] input { text-align: left; }
    .stDataFrame { border: 1px solid #f0f2f6; border-radius: 10px; }
    .group-title { padding: 8px 15px; background-color: #f1f3f5; border-left: 6px solid #495057; font-weight: bold; font-size: 1.1em; margin-bottom: 15px; margin-top: 20px; color: #212529; }
    .price-analysis { padding: 15px; background-color: #fff4e6; border-radius: 10px; border: 1px solid #ffd8a8; margin-bottom: 20px; font-size: 1.05em; line-height: 1.6; }
    
    .notice-card {
        padding: 18px;
        background-color: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        line-height: 1.6 !important;
        color: #495057;
        white-space: pre-wrap !important; /* 이 코드가 줄 바꿈과 자간을 보존합니다 */
        text-align: left !important;
    }
    .notice-info { font-size: 0.8em; color: #adb5bd; margin-bottom: 8px; font-weight: 700; text-align: left; }
    .stExpander { border: 1px solid #f1f3f5 !important; border-radius: 8px !important; margin-bottom: 5px !important; }
    
    div[data-testid="stSelectbox"] > label, 
    div[data-testid="stTextInput"] > label,
    div[data-testid="stTextArea"] > label {
        font-size: 1.1em !important; font-weight: 800 !important; color: #d9480f !important;
    }
    </style>
""", unsafe_allow_html=True)

db = load_data(DB_PATH)
ndb = load_data(NOTICE_PATH)

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# [3] 사이드바 - 호칭 수정 및 노출 제어
st.sidebar.title(f"🚀 운영 관리자 v155.11")
menu = st.sidebar.selectbox("메뉴 선택", ["🏠 MD 포털", "🔐 관리자 통합 센터"])

if menu == "🔐 관리자 통합 센터":
    if not st.session_state.authenticated:
        pwd_input = st.sidebar.text_input("PASSWORD", type="password")
        if st.sidebar.button("🔓 로그인", use_container_width=True):
            if pwd_input == "1234":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.sidebar.error("비밀번호가 틀렸습니다.")
    else:
        if st.sidebar.button("🔒 로그아웃", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

if menu == "🏠 MD 포털":
    st.title("🚀 핫딜 전략 통합 포털")
    
    col_left, col_right = st.columns(2, gap="large")
    
    with col_left:
        st.subheader("📢 공지사항")
        notices = ndb[ndb["유형"] == "공지사항"] if not ndb.empty else pd.DataFrame()
        if not notices.empty:
            for idx, r in notices.tail(5).iloc[::-1].iterrows():
                with st.expander(f"📌 [{r['날짜']}] {r['제목']}", expanded=False):
                    st.markdown(f"""
                    <div class="notice-card">
                        <div class="notice-info">📂 NOTICE | {r['날짜']}</div>
                        <div style="font-weight:800; margin-bottom:12px; font-size:1.1em; color:#343a40;">{r['제목']}</div>
                        <div style="text-align: left;">{r['내용']}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("등록된 공지사항이 없습니다.")
        
    with col_right:
        st.subheader("🚀 업데이트")
        updates = ndb[ndb["유형"] == "업데이트"] if not ndb.empty else pd.DataFrame()
        if not updates.empty:
            for idx, r in updates.tail(5).iloc[::-1].iterrows():
                with st.expander(f"⚙️ [{r['날짜']}] {r['제목']}", expanded=False):
                    st.markdown(f"""
                    <div class="notice-card">
                        <div class="notice-info">📂 UPDATE | {r['날짜']}</div>
                        <div style="font-weight:800; margin-bottom:12px; font-size:1.1em; color:#343a40;">{r['제목']}</div>
                        <div style="text-align: left;">{r['내용']}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("업데이트 내역이 없습니다.")
    
    st.divider()
    # 데이터 조회 영역 (이하 동일)
    p_list = ["전체"] + sorted([str(p) for p in db["플랫폼"].unique().tolist() if str(p).strip() != ""]) if not db.empty else ["전체"]
    col_q, col_p, col_s1, col_s2 = st.columns([2, 1, 1, 1], gap="small")
    with col_q: search_q = st.text_input("브랜드/제품명 검색", value="", placeholder="검색어 입력") 
    with col_p: platform_filter = st.selectbox("플랫폼 필터", p_list)
    with col_s1: sort_by = st.selectbox("정렬 기준", ["📅 행사일정순", "💰 최종혜택가순"])
    with col_s2: sort_order = st.selectbox("정렬 순서", ["⬇️ 내림차순", "⬆️ 오름차순"])

    if not db.empty:
        if search_q.strip() or platform_filter != "전체":
            res = db.copy()
            if search_q: res = res[res["브랜드"].str.contains(search_q, case=False) | res["제품명"].str.contains(search_q, case=False)]
            if platform_filter != "전체": res = res[res["플랫폼"] == platform_filter]
            if not res.empty:
                res["_tmp_price"] = res["최종혜택가"].apply(extract_num)
                min_row = res.loc[res["_tmp_price"].idxmin()]; st.markdown(f'<div class="price-analysis">💡 <b>최저가 가이드:</b> 현재 최저가는 <b>{int(min_row["_tmp_price"]):,}원</b>입니다.</div>', unsafe_allow_html=True)
                is_asc = True if "오름차순" in sort_order else False
                res["_tmp_date"] = res["행사일정"].str.split(" ~ ").str[0]
                res = res.sort_values(by="_tmp_date" if "행사일정" in sort_by else "_tmp_price", ascending=is_asc)
                st.dataframe(res[DISPLAY_COLS], use_container_width=True, hide_index=True)
            else: st.warning("🔍 검색 결과가 없습니다.")
        else: st.markdown('<div style="padding:40px; text-align:center; color:#adb5bd;">🔍 검색어를 입력하거나 플랫폼을 선택하여 데이터를 조회하세요.</div>', unsafe_allow_html=True)

elif menu == "🔐 관리자 통합 센터":
    if st.session_state.authenticated:
        st.title("🔐 관리자 시스템")
        t1, t2, t3 = st.tabs(["✨ 핫딜 등록", "📝 데이터 수정/삭제", "📢 게시물 관리"])
        
        # ... (이하 관리자 탭 로직은 이전과 동일하게 유지)
        with t1:
            st.markdown('<div class="group-title">📂 카테고리/플랫폼 설정</div>', unsafe_allow_html=True)
            cat_choice = st.selectbox("카테고리 선택", list(BRAND_DICT.keys()))
            c_pf1, c_pf2 = st.columns(2)
            pf_manual = c_pf2.text_input("플랫폼 직접 입력")
            pf_sel = c_pf1.selectbox("플랫폼 선택", ["지마켓", "옥션", "11번가", "쿠팡", "네이버", "SSG"], disabled=len(pf_manual.strip()) > 0)
            st.markdown('<div class="group-title">🏷️ 제품 정보</div>', unsafe_allow_html=True)
            brand_manual = st.text_input("브랜드 직접 입력")
            brand_sel = st.selectbox("대표 브랜드 선택", sorted(BRAND_DICT.get(cat_choice, [])), disabled=len(brand_manual.strip()) > 0)
            prod_input = st.text_input("제품명 입력 (필수*)") 
            st.markdown('<div class="group-title">💰 금액 설정</div>', unsafe_allow_html=True)
            price_raw = st.text_input("정상가 (원)", value="", placeholder="0")
            c_h1, c_h2 = st.columns(2)
            co_v_raw = c_h1.text_input("쿠폰 할인", value="", key="reg_cov", placeholder="0"); co_t = c_h1.radio("단위", ["원", "%"], horizontal=True, key="reg_cot")
            ca_v_raw = c_h2.text_input("카드 할인", value="", key="reg_cav", placeholder="0"); ca_t = c_h2.radio("단위", ["원", "%"], horizontal=True, key="reg_cat")
            price = extract_num(price_raw); co_v = extract_num(co_v_raw); ca_v = extract_num(ca_v_raw)
            calc_co = co_v if co_t == "원" else (price * (co_v/100))
            calc_ca = ca_v if ca_t == "원" else (price * (calc_ca/100))
            final_preview = int(price - calc_co - calc_ca)
            st.markdown(f'<div class="price-analysis">🔍 <b>최종 혜택가:</b> <span style="font-size:1.4em; color:#e03131;">{final_preview:,}원</span></div>', unsafe_allow_html=True)
            st.markdown('<div class="group-title">📅 일정/기타</div>', unsafe_allow_html=True)
            event_date = st.date_input("행사 일정", [date.today(), date.today()])
            gift = st.text_area("사은품 및 비고")
            if st.button("🚀 최종 등록", use_container_width=True):
                if not prod_input or price == 0: st.error("필수 입력 확인!")
                else:
                    pf_f = pf_manual if pf_manual.strip() else pf_sel; br_f = brand_manual if brand_manual.strip() else brand_sel
                    dr = f"{event_date[0]} ~ {event_date[1]}" if len(event_date) == 2 else str(event_date[0])
                    new_row = pd.DataFrame([{"선택": False, "등록날짜": datetime.now().strftime("%Y-%m-%d"), "카테고리": cat_choice, "플랫폼": pf_f, "브랜드": br_f, "제품명": prod_input, "정상가": f"{int(price):,}원", "행사일정": dr, "쿠폰혜택": f"{fmt_num(co_v)}{co_t}", "카드혜택": f"{fmt_num(ca_v)}{ca_t}", "최종혜택가": f"{final_preview:,}원", "사은품": gift}])
                    pd.concat([db, new_row], ignore_index=True).to_csv(DB_PATH, index=False, encoding="utf-8-sig")
                    st.success("등록 완료!"); time.sleep(1); st.cache_data.clear(); st.rerun()

        with t2:
            st.subheader("📝 데이터 수정/삭제")
            if not db.empty:
                edited_db = st.data_editor(db, use_container_width=True, hide_index=True)
                if st.button("💾 변경사항 저장", use_container_width=True):
                    edited_db.to_csv(DB_PATH, index=False, encoding="utf-8-sig"); st.toast("✅ 저장 완료!"); st.cache_data.clear(); st.rerun()
                if st.button("🗑️ 선택 삭제", use_container_width=True):
                    edited_db[edited_db["선택"] == False].to_csv(DB_PATH, index=False, encoding="utf-8-sig"); st.toast("🗑️ 삭제 완료!"); st.cache_data.clear(); st.rerun()

        with t3:
            st.subheader("📢 게시물 통합 관리")
            with st.expander("🆕 새 게시글 작성하기", expanded=True):
                n_type = st.selectbox("유형", ["공지사항", "업데이트"], key="new_nt_type")
                n_title = st.text_input("제목", key="new_nt_title")
                n_content = st.text_area("내용", key="new_nt_content", height=200)
                if st.button("✅ 게시글 등록", use_container_width=True):
                    if n_title and n_content:
                        new_n = pd.DataFrame([{"선택":False, "날짜":datetime.now().strftime("%Y-%m-%d"), "유형":n_type, "제목":n_title, "내용":n_content}])
                        pd.concat([ndb, new_n], ignore_index=True).to_csv(NOTICE_PATH, index=False, encoding="utf-8-sig")
                        st.success("등록 성공!"); time.sleep(1); st.cache_data.clear(); st.rerun()

            st.markdown('<div class="group-title">📋 게시물 목록</div>', unsafe_allow_html=True)
            if not ndb.empty:
                if 'edit_idx' not in st.session_state: st.session_state.edit_idx = None
                for idx in reversed(range(len(ndb))):
                    row = ndb.iloc[idx]
                    col_info, col_btns = st.columns([8, 2])
                    with col_info: st.markdown(f"**[{row['날짜']}] ({row['유형']})** {row['제목']}")
                    with col_btns:
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button("✏️", key=f"edit_btn_{idx}"): st.session_state.edit_idx = idx; st.rerun()
                        with b2:
                            if st.button("🗑️", key=f"del_btn_{idx}"):
                                ndb = ndb.drop(idx).reset_index(drop=True); ndb.to_csv(NOTICE_PATH, index=False, encoding="utf-8-sig")
                                st.toast(f"🗑️ 삭제 완료!"); time.sleep(1); st.cache_data.clear(); st.rerun()
                    st.divider()

                if st.session_state.edit_idx is not None:
                    edit_idx = st.session_state.edit_idx; edit_row = ndb.iloc[edit_idx]
                    st.markdown(f'<div style="padding:15px; background:#fff9db; border-radius:10px; margin-bottom:15px;">✏️ <b>"{edit_row["제목"]}"</b> 수정 중...</div>', unsafe_allow_html=True)
                    new_title = st.text_input("제목 수정", value=edit_row['제목'])
                    new_content = st.text_area("내용 수정", value=edit_row['내용'], height=250)
                    eb1, eb2 = st.columns(2)
                    with eb1:
                        if st.button("💾 수정 저장", use_container_width=True):
                            ndb.at[edit_idx, '제목'] = new_title; ndb.at[edit_idx, '내용'] = new_content
                            ndb.to_csv(NOTICE_PATH, index=False, encoding="utf-8-sig"); st.success("저장 완료!"); st.session_state.edit_idx = None; time.sleep(1); st.cache_data.clear(); st.rerun()
                    with eb2:
                        if st.button("❌ 취소", use_container_width=True): st.session_state.edit_idx = None; st.rerun()
    else:
        st.warning("🔐 관리자 시스템을 이용하려면 '메뉴 선택'에서 '🔐 관리자 통합 센터'를 선택한 후 비밀번호를 입력해 주세요.")