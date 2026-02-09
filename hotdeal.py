import streamlit as st
import pandas as pd
import os
from datetime import datetime, date

# [1] 데이터 로드 및 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "hotdeal_master_db.csv")
NOTICE_PATH = os.path.join(BASE_DIR, "hotdeal_notice_db.csv")

DISPLAY_COLS = [
    "플랫폼", "행사일정", "브랜드", "제품명", "정상가", 
    "쿠폰혜택", "카드혜택", "최종혜택가", "사은품"
]

def extract_num(val):
    try:
        if pd.isna(val) or val == "": return 0
        if isinstance(val, (int, float)): return int(val)
        clean_val = "".join(filter(str.isdigit, str(val)))
        return int(clean_val) if clean_val else 0
    except: return 0

@st.cache_data(ttl=1)
def load_data(path):
    if not os.path.exists(path):
        if "master" in path:
            return pd.DataFrame(columns=["선택", "등록날짜", "카테고리"] + DISPLAY_COLS)
        return pd.DataFrame(columns=["선택", "날짜", "유형", "제목", "내용"])
    
    df = pd.read_csv(path).fillna("")
    if "선택" not in df.columns: 
        df.insert(0, "선택", False)
    df["선택"] = df["선택"].astype(bool)
    
    if "master" in path:
        if "플랫폼" not in df.columns: df["플랫폼"] = "미지정"
        for col in ["플랫폼", "브랜드", "제품명", "최종혜택가", "행사일정", "카테고리"]:
            if col in df.columns: df[col] = df[col].astype(str)
        cols = ["선택"] + [c for c in df.columns if c != "선택"]
        df = df[cols]
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
st.markdown("""
    <style>
    button[data-testid="stNumberInputStepUp"], button[data-testid="stNumberInputStepDown"] { display: none !important; }
    div[data-testid="stNumberInput"] div[role="group"] { display: none !important; }
    .stDataFrame { border: 1px solid #f0f2f6; border-radius: 10px; }
    .search-guide { padding: 20px; border: 2px dashed #d1e3f8; border-radius: 10px; text-align: center; color: #5c7cfa; background-color: #f8f9fa; }
    .group-title { padding: 5px 10px; background-color: #e7f5ff; border-left: 5px solid #228be6; font-weight: bold; margin-bottom: 15px; margin-top: 10px; }
    .price-analysis { padding: 15px; background-color: #fff4e6; border-radius: 10px; border: 1px solid #ffd8a8; margin-bottom: 20px; font-size: 1.05em; line-height: 1.6; }
    /* 관리자 경고 문구 스타일 */
    .admin-warning { color: #e03131; font-weight: bold; font-size: 1.2em; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

def highlight_final_price(s):
    return ['background-color: #FFF9C4; font-weight: bold; color: #E65100' if s.name == '최종혜택가' else '' for _ in s]

db = load_data(DB_PATH)
ndb = load_data(NOTICE_PATH)

st.sidebar.title("🚀 SPEED MASTER v142.0")
menu = st.sidebar.selectbox("메뉴 선택", ["🏠 메인 홈 (MD 포털)", "🔐 관리자 통합 센터"])

# --- 🏠 1. 메인 홈 ---
if menu == "🏠 메인 홈 (MD 포털)":
    st.title("🚀 핫딜 전략 통합 포털")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📢 중요 공지 및 업데이트")
        if not ndb.empty:
            for _, row in ndb.tail(3).iloc[::-1].iterrows():
                if str(row['유형']) == "공지사항": st.info(f"**📢 [공지] {row['제목']}** ({row['날짜']})\n\n{row['내용']}")
                else: st.success(f"**🚀 [업데이트] {row['제목']}** ({row['날짜']})\n\n{row['내용']}")
    with c2:
        st.subheader("📊 실시간 핫딜 현황")
        m1, m2 = st.columns(2)
        m1.metric("📦 누적 핫딜", f"{len(db)}건")
        today_c = len(db[db["등록날짜"] == datetime.now().strftime("%Y-%m-%d")]) if not db.empty else 0
        m2.metric("🔥 오늘 등록", f"{today_c}건")

    st.divider()
    if not db.empty:
        p_list_raw = db["플랫폼"].unique().tolist()
        p_list = ["전체"] + sorted([str(p) for p in p_list_raw if str(p).strip() != ""])
    else: p_list = ["전체"]

    col_q, col_p, col_s1, col_s2 = st.columns([2, 1, 1, 1], gap="small")
    with col_q: search_q = st.text_input("브랜드/제품명 검색", value="", placeholder="검색어 입력") 
    with col_p: platform_filter = st.selectbox("플랫폼 필터", p_list)
    with col_s1: sort_by = st.selectbox("정렬 기준", ["📅 행사일정순", "💰 최종혜택가순"])
    with col_s2: sort_order = st.selectbox("정렬 순서", ["⬇️ 내림차순", "⬆️ 오름차순"])

    if not db.empty:
        if search_q.strip() or platform_filter != "전체":
            res = db.copy()
            if search_q:
                res = res[res["브랜드"].str.contains(search_q, case=False) | res["제품명"].str.contains(search_q, case=False)]
            if platform_filter != "전체":
                res = res[res["플랫폼"] == platform_filter]
            
            if not res.empty:
                res["_tmp_price"] = res["최종혜택가"].apply(extract_num)
                min_row = res.loc[res["_tmp_price"].idxmin()]
                min_price = min_row["_tmp_price"]
                min_date = min_row["행사일정"]
                
                st.markdown(f"""
                <div class="price-analysis">
                    💡 <b>핫딜 전략 통합 포털 기준:</b> 최저가는 <b>{min_price:,}원</b>이며, 가장 저렴했던 일정은 <b>{min_date}</b>입니다.
                </div>
                """, unsafe_allow_html=True)

                is_asc = True if "오름차순" in sort_order else False
                res["_tmp_date"] = res["행사일정"].str.split(" ~ ").str[0]
                res = res.sort_values(by="_tmp_date" if "행사일정" in sort_by else "_tmp_price", ascending=is_asc)
                st.dataframe(res[DISPLAY_COLS].style.apply(highlight_final_price, axis=0), use_container_width=True, hide_index=True)
            else: st.warning("🔍 검색 결과가 없습니다.")
        else:
            st.markdown('<div class="search-guide">🔍 확인하시려는 <b>브랜드, 제품명</b>을 입력하거나 <b>플랫폼</b>을 선택해 주세요.</div>', unsafe_allow_html=True)

# --- 🔐 2. 관리자 통합 센터 ---
elif menu == "🔐 관리자 통합 센터":
    st.title("🔐 관리자 시스템")
    # [v142] 형님 요청대로 강력한 경고 문구 추가!
    st.sidebar.markdown('<p class="admin-warning">🛑 관계자 외 출입금지</p>', unsafe_allow_html=True)
    if st.sidebar.text_input("PASSWORD", type="password", placeholder="비밀번호를 입력하세요") == "1234":
        t1, t2, t3 = st.tabs(["✨ 핫딜 등록 & 분석", "🗑️ 데이터 관리 및 삭제", "📢 게시물 관리"])
        
        with t1:
            with st.form("admin_input_v142", clear_on_submit=True):
                st.markdown('<div class="group-title">📍 플랫폼 설정</div>', unsafe_allow_html=True)
                pf_options = ["지마켓", "옥션", "11번가", "쿠팡", "네이버", "카카오", "SSG", "롯데온", "컬리"]
                pf_sel = st.selectbox("플랫폼 선택", pf_options, index=None, placeholder="눌러서 선택해주세요")
                pf_manual = st.text_input("플랫폼 직접 입력 (비워두면 위 선택 적용)", placeholder="위 선택지에 없을 때만 입력")
                
                st.markdown('<div class="group-title">🏷️ 카테고리 및 브랜드 설정</div>', unsafe_allow_html=True)
                cat = st.selectbox("카테고리 선택", list(BRAND_DICT.keys()))
                learned = db[db["카테고리"] == cat]["브랜드"].unique().tolist() if not db.empty else []
                total_b = sorted(list(set(BRAND_DICT.get(cat, []) + learned)))
                brand_sel = st.selectbox("대표 브랜드 선택", total_b, index=None, placeholder="눌러서 선택해주세요")
                brand_manual = st.text_input("신규 브랜드 직접 입력")
                
                st.markdown('<div class="group-title">🔍 제품명 및 금액 설정</div>', unsafe_allow_html=True)
                prod_input = st.text_input("제품명 (분석 및 등록)", placeholder="제품명을 입력하세요") 
                price = st.number_input("정상가 (원)", min_value=0, value=None, step=100, placeholder="숫자만 입력")
                
                st.markdown('<div class="group-title">📅 행사일정 및 할인값 설정</div>', unsafe_allow_html=True)
                event_date = st.date_input("행사 일정 선택", [date.today(), date.today()])
                
                c_h1, c_h2 = st.columns(2)
                with c_h1:
                    co_v = st.number_input("쿠폰 할인값", min_value=0.0, value=None, placeholder="할인액/율 입력")
                    co_t = st.radio("쿠폰 단위", ["원", "%"], horizontal=True)
                with c_h2:
                    ca_v = st.number_input("카드 할인값", min_value=0.0, value=None, placeholder="할인액/율 입력")
                    ca_t = st.radio("카드 단위", ["원", "%"], horizontal=True)
                
                gift = st.text_area("사은품 및 비고", placeholder="사은품 내용을 입력하세요")
                
                submit = st.form_submit_button("🚀 분석 완료 및 최종 마스터 DB 등록", use_container_width=True)
                
            if submit:
                pf_final = pf_manual if pf_manual else pf_sel
                brand_final = brand_manual if brand_manual else brand_sel
                
                if pf_final and brand_final and prod_input and price:
                    v_co, v_ca = co_v or 0.0, ca_v or 0.0
                    c_co = int(v_co) if co_t == "원" else int(price * (v_co/100))
                    c_ca = int(v_ca) if ca_t == "원" else int(price * (v_ca/100))
                    f_price = price - c_co - c_ca
                    
                    if not db.empty:
                        hist_match = db[db["제품명"].str.contains(prod_input, case=False, na=False)]
                        if not hist_match.empty:
                            past_avg = hist_match["최종혜택가"].apply(extract_num).mean()
                            if f_price < past_avg: st.balloons()
                    
                    dr = f"{event_date[0]} ~ {event_date[1]}" if len(event_date) == 2 else str(event_date[0])
                    new_row = pd.DataFrame([{
                        "선택": False, "등록날짜": datetime.now().strftime("%Y-%m-%d"), "카테고리": cat,
                        "플랫폼": str(pf_final), "브랜드": str(brand_final), "제품명": str(prod_input),
                        "정상가": f"{price:,}원", "행사일정": dr, "쿠폰혜택": f"{int(v_co):,}원" if co_t=="원" else f"{v_co}%",
                        "카드혜택": f"{int(v_ca):,}원" if ca_t=="원" else f"{v_ca}%", "최종혜택가": f"{f_price:,}원", "사은품": gift
                    }])
                    pd.concat([db, new_row], ignore_index=True).to_csv(DB_PATH, index=False, encoding="utf-8-sig")
                    st.cache_data.clear(); st.success("✅ 등록 완료!"); st.rerun()

        with t2:
            st.subheader("🗑️ 데이터 관리 및 삭제")
            if not db.empty:
                edited_db = st.data_editor(db, use_container_width=True, hide_index=True)
                c_del, c_save = st.columns([1, 5])
                if c_del.button("🗑️ 선택 삭제", type="primary"):
                    edited_db[edited_db["선택"] == False].to_csv(DB_PATH, index=False, encoding="utf-8-sig")
                    st.cache_data.clear(); st.rerun()
                if c_save.button("💾 수정사항 저장"):
                    edited_db.to_csv(DB_PATH, index=False, encoding="utf-8-sig")
                    st.cache_data.clear(); st.success("저장 완료!"); st.rerun()

        with t3:
            st.subheader("📢 게시물 관리")
            with st.form("notice_form_v142", clear_on_submit=True):
                n_type, n_title, n_content = st.selectbox("유형", ["공지사항", "업데이트"]), st.text_input("제목"), st.text_area("내용")
                if st.form_submit_button("✅ 게시글 등록"):
                    new_n = pd.DataFrame([{"선택": False, "날짜": datetime.now().strftime("%Y-%m-%d"), "유형": n_type, "제목": n_title, "내용": n_content}])
                    pd.concat([load_data(NOTICE_PATH), new_n], ignore_index=True).to_csv(NOTICE_PATH, index=False, encoding="utf-8-sig")
                    st.cache_data.clear(); st.success("게시 완료!"); st.rerun()