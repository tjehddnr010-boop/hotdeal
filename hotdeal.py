# v165.10 - 사이드바 기본 닫힘 설정 재확인 및 기타 기능 유지 버전

import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
import time
from difflib import get_close_matches

# =================================================================
# 📢 런칭 전 필수 설정
# =================================================================
KAKAO_LINK = "https://open.kakao.com/o/gQshP8fi" 
# =================================================================

# [1] 데이터 로드 및 초기 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "hotdeal_master_db.csv")
NOTICE_PATH = os.path.join(BASE_DIR, "hotdeal_notice_db.csv")

DISPLAY_COLS = ["플랫폼", "행사일정", "브랜드", "제품명", "정상가", "최종혜택가", "체감가", "사은품"]

def extract_num(val):
    try:
        if pd.isna(val) or val == "" or val is None: return 0.0
        if isinstance(val, (int, float)): return float(val)
        clean_val = "".join(filter(lambda x: x.isdigit() or x == '.', str(val)))
        return float(clean_val) if clean_val else 0.0
    except: return 0.0

def format_korean_unit(num):
    num = int(num)
    if num == 0: return "0원"
    if num >= 100000000:
        return f"{num//100000000}억 {(num%100000000)//10000}만 {num%10000:,}원"
    if num >= 10000:
        return f"{num//10000}만 {num%10000:,}원"
    return f"{num:,}원"

@st.cache_data(ttl=1)
def load_data(path):
    is_master = "master" in path
    if not os.path.exists(path):
        if is_master: return pd.DataFrame(columns=["선택", "등록날짜", "카테고리"] + DISPLAY_COLS + ["표준모델명"])
        return pd.DataFrame(columns=["선택", "날짜", "유형", "제목", "내용"])
    df = pd.read_csv(path).fillna("")
    if "선택" not in df.columns: df.insert(0, "선택", False)
    df["선택"] = df["선택"].astype(bool)
    if is_master and "표준모델명" not in df.columns:
        df["표준모델명"] = df["제품명"] if "제품명" in df.columns else ""
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

# [2] 페이지 설정 - 사이드바 닫힘 상태 고정
st.set_page_config(
    page_title="HOTDEAL STRATEGY HUB", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# [3] 맞춤형 CSS
st.markdown("""
    <style>
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');
    div[data-testid="stTextInput"] input { text-align: left; }
    .group-title { padding: 10px 18px; background-color: #f8f9fa; border-left: 6px solid #343a40; font-weight: 800; font-size: 1.2em; margin-bottom: 18px; margin-top: 25px; color: #212529; }
    .unified-banner { padding: 18px; background-color: #fff9db; border-radius: 12px; border: 2px solid #ffec99; margin-bottom: 22px; font-size: 1.15em !important; line-height: 1.7; color: #333; box-shadow: 0 2px 5px rgba(0,0,0,0.03); }
    .accent-price { color: #d9480f; font-weight: 800; }
    .guide-mention { color: #f08c00; font-weight: 900; margin-left: 15px; border-left: 3px solid #ffe066; padding-left: 12px; }
    div[data-testid="stSelectbox"] > label, div[data-testid="stTextInput"] > label, div[data-testid="stTextArea"] > label { font-size: 1.1em !important; font-weight: 900 !important; color: #e67e22 !important; }
    .kakao-container { display: flex; justify-content: flex-end; align-items: center; height: 100%; padding-top: 25px; }
    .kakao-btn { display: inline-flex; align-items: center; justify-content: center; padding: 12px 24px; background-color: #FEE500; color: #3C1E1E !important; border-radius: 30px; font-weight: 800; text-decoration: none !important; font-size: 0.95em; box-shadow: 0 4px 15px rgba(254, 229, 0, 0.3); border: 1px solid #FADA00; }
    .notice-card { padding: 22px; background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 12px; line-height: 1.8; color: #495057; text-align: left !important; }
    
    .empty-guide { 
        color: #909294; 
        font-size: 1.1em; 
        font-weight: 500; 
        padding: 50px 0; 
        text-align: center; 
        border: 1px dashed #e9ecef; 
        border-radius: 12px; 
        background-color: #fcfcfc; 
        margin: 20px 0;
        letter-spacing: -0.5px;
    }
    .smart-viewer { background-color: #2b3035; color: #ffffff; padding: 10px 18px; border-radius: 8px; font-size: 1.1em; font-weight: 700; margin-bottom: 15px; border-left: 6px solid #fcc419; }
    </style>
""", unsafe_allow_html=True)

db = load_data(DB_PATH)
ndb = load_data(NOTICE_PATH)

if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'prod_val' not in st.session_state: st.session_state.prod_val = ""

# [4] 사이드바 내비게이션
st.sidebar.title(f"🚀 운영 관리자 v165.10")
menu = st.sidebar.selectbox("메뉴 선택", ["🏠 MD 포털", "🔐 관리자 통합 센터"])

if menu == "🔐 관리자 통합 센터":
    if not st.session_state.authenticated:
        pwd = st.sidebar.text_input("PASSWORD", type="password")
        if st.sidebar.button("🔓 로그인", use_container_width=True):
            if pwd == "1234": st.session_state.authenticated = True; st.rerun()
            else: st.sidebar.error("비밀번호 불일치")
    else:
        if st.sidebar.button("🔒 로그아웃", use_container_width=True): st.session_state.authenticated = False; st.rerun()

# [5] 🏠 MD 포털 화면
if menu == "🏠 MD 포털":
    h_col1, h_col2 = st.columns([4, 1.2])
    with h_col1: st.title("🚀 핫딜 전략 통합 포털")
    with h_col2: st.markdown(f'''<div class="kakao-container"><a href="{KAKAO_LINK}" target="_blank" class="kakao-btn"><i class="fa-solid fa-comment"></i> 오류 신고 및 제안</a></div>''', unsafe_allow_html=True)
    
    col_l, col_r = st.columns(2, gap="large")
    with col_l:
        st.subheader("📢 공지사항")
        notices = ndb[ndb["유형"] == "공지사항"] if not ndb.empty else pd.DataFrame()
        if not notices.empty:
            for idx, r in notices.tail(5).iloc[::-1].iterrows():
                with st.expander(f"📌 [{r['날짜']}] {r['제목']}"):
                    st.markdown(f'<div class="notice-card"><b>{r["제목"]}</b><br><br>{r["내용"]}</div>', unsafe_allow_html=True)
    with col_r:
        st.subheader("🚀 업데이트")
        updates = ndb[ndb["유형"] == "업데이트"] if not ndb.empty else pd.DataFrame()
        if not updates.empty:
            for idx, r in updates.tail(5).iloc[::-1].iterrows():
                with st.expander(f"⚙️ [{r['날짜']}] {r['제목']}"):
                    st.markdown(f'<div class="notice-card"><b>{r["제목"]}</b><br><br>{r["내용"]}</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="group-title">🔍 핫딜 데이터 조회 및 분석</div>', unsafe_allow_html=True)
    p_list = ["전체"] + sorted([str(p) for p in db["플랫폼"].unique().tolist() if str(p).strip() != ""]) if not db.empty else ["전체"]
    cq, cp, cs1, cs2 = st.columns([2, 1, 1, 1], gap="small")
    search_q = cq.text_input("브랜드/제품명/모델명 검색", value="", placeholder="검색어를 입력하세요", key="p_q_v55")
    pf_f = cp.selectbox("플랫폼 필터", p_list, key="p_p_v55")
    s_by = cs1.selectbox("정렬 기준", ["📅 행사일정순", "💰 최종혜택가순"], key="p_s_v55")
    s_or = cs2.selectbox("정렬 순서", ["⬇️ 내림차순", "⬆️ 오름차순"], key="p_o_v55")

    if (search_q.strip() or pf_f != "전체") and not db.empty:
        res = db.copy()
        if search_q: res = res[res["브랜드"].str.contains(search_q, case=False) | res["제품명"].str.contains(search_q, case=False) | res["표준모델명"].str.contains(search_q, case=False)]
        if pf_f != "전체": res = res[res["플랫폼"] == pf_f]
        
        if not res.empty:
            res["_tf"] = res["최종혜택가"].apply(extract_num); res["_te"] = res["체감가"].apply(extract_num)
            min_f, min_e = int(res["_tf"].min()), int(res["_te"].min())
            st.markdown(f'''<div class="unified-banner">💡 <b>"{search_q if search_q else pf_f}" 검색 결과:</b> 최종 최저 <span class="accent-price">{min_f:,}원</span> | ✨ 체감 최저 <span class="accent-price">{min_e:,}원</span> <span class="guide-mention">🔍 상세 사은품 구성을 꼭 확인하세요!</span></div>''', unsafe_allow_html=True)
            is_a = True if "오름차순" in s_or else False
            if "행사일정" in s_by:
                res["_td"] = res["행사일정"].str.split(" ~ ").str[0]; res = res.sort_values(by="_td", ascending=is_a)
            else: res = res.sort_values(by="_tf", ascending=is_a)
            st.dataframe(res[DISPLAY_COLS], use_container_width=True, hide_index=True)
        else:
            st.warning("검색 결과가 없습니다.")
    else:
        st.markdown('<div class="empty-guide"><i class="fa-solid fa-magnifying-glass"></i> 검색어를 입력하시면 상세 데이터가 나타납니다.</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="group-title">📊 MD 가격 시뮬레이터 (시장가 비교분석)</div>', unsafe_allow_html=True)
    sc1, sc2, sc3 = st.columns([2, 1, 1])
    with sc1: s_name = st.text_input("분석할 제품명 입력", placeholder="예: 인존 버즈", key="sim_n_v55")
    with sc2:
        s_p = st.text_input("예상 최종혜택가(원)", value="", key="sim_p_v55")
        if s_p and extract_num(s_p) > 0: st.markdown(f'<div class="smart-viewer">💰 {format_korean_unit(extract_num(s_p))}</div>', unsafe_allow_html=True)
    with sc3:
        s_f = st.text_input("예상 체감가(원)", value="", key="sim_f_v55")
        if s_f and extract_num(s_f) > 0: st.markdown(f'<div class="smart-viewer">✨ {format_korean_unit(extract_num(s_f))}</div>', unsafe_allow_html=True)

    if s_name and not db.empty:
        input_p, input_f = extract_num(s_p), extract_num(s_f)
        sim_res = db[db["표준모델명"].str.contains(s_name, case=False) | db["제품명"].str.contains(s_name, case=False)].copy()
        
        if not sim_res.empty:
            sim_res["_f_val"] = sim_res["최종혜택가"].apply(extract_num)
            sim_res["_e_val"] = sim_res["체감가"].apply(extract_num)
            h_min_f = int(sim_res["_f_val"].min())
            h_min_e = int(sim_res[sim_res["_e_val"] > 0]["_e_val"].min()) if not sim_res[sim_res["_e_val"] > 0].empty else h_min_f
            
            st.markdown(f'''<div class="unified-banner">🔎 <b>"{s_name}"</b> 과거 기록: 최종혜택 최저 <span class="accent-price">{h_min_f:,}원</span> | ✨ 체감 최저 <span class="accent-price">{h_min_e:,}원</span></div>''', unsafe_allow_html=True)
            
            def get_judgment(current, historic):
                if current <= 0: return None
                if current < historic: return ("🔥 핫딜 무조건 진행해보죠!", "success")
                elif current <= historic * 1.1: return ("👍 핫딜 해볼까요? (10% 내외)", "info")
                elif current <= historic * 1.2: return ("🤔 핫딜 조금 어렵지 않을까요? (20% 내외)", "warning")
                else: return ("❌ 핫딜 안될 거 같아요!", "error")

            res_p, res_f = get_judgment(input_p, h_min_f), get_judgment(input_f, h_min_e)
            jc1, jc2 = st.columns(2)
            if res_p:
                with jc1:
                    st.write("**[최종혜택가 판단]**")
                    if res_p[1] == "success": st.success(res_p[0])
                    elif res_p[1] == "info": st.info(res_p[0])
                    elif res_p[1] == "warning": st.warning(res_p[0])
                    else: st.error(res_p[0])
            if res_f:
                with jc2:
                    st.write("**[체감가 판단]**")
                    if res_f[1] == "success": st.success(res_f[0])
                    elif res_f[1] == "info": st.info(res_f[0])
                    elif res_f[1] == "warning": st.warning(res_f[0])
                    else: st.error(res_f[0])
        else: st.info("과거 데이터가 없습니다.")
    else:
        st.markdown('<div class="empty-guide"><i class="fa-solid fa-magnifying-glass-chart"></i> 분석하실 품목을 입력하시면 핫딜 가능 여부에 대한 데이터가 나타납니다.</div>', unsafe_allow_html=True)

# [6] 🔐 관리자 통합 센터
elif menu == "🔐 관리자 통합 센터" and st.session_state.authenticated:
    st.title("🔐 관리자 시스템")
    t1, t2, t3 = st.tabs(["✨ 핫딜 등록", "📝 데이터 수정/삭제", "📢 게시물 관리"])
    
    with t1:
        st.markdown('<div class="group-title">📂 카테고리/플랫폼 설정</div>', unsafe_allow_html=True)
        cat = st.selectbox("카테고리 선택", list(BRAND_DICT.keys()), key="ad_cat")
        cp1, cp2 = st.columns(2)
        pf_s = cp1.selectbox("플랫폼 선택", ["지마켓", "옥션", "11번가", "쿠팡", "네이버", "SSG"], key="ad_pfs")
        pf_m = cp2.text_input("플랫폼 직접 입력", key="ad_pfm")
        st.markdown('<div class="group-title">🏷️ 제품 정보 및 매칭</div>', unsafe_allow_html=True)
        cb1, cb2 = st.columns(2)
        br_s = cb1.selectbox("대표 브랜드 선택", sorted(BRAND_DICT.get(cat, [])), key="ad_brs")
        br_m = cb2.text_input("브랜드 직접 입력", key="ad_brm")
        prod = st.text_input("제품명 입력", value=st.session_state.prod_val, key="ad_prod")
        std = prod
        if prod and not db.empty:
            all_m = db["표준모델명"].unique().tolist()
            matches = get_close_matches(prod, all_m, n=5, cutoff=0.2)
            if matches:
                st.markdown('<span style="color:#1c7ed6; font-size:0.9em; font-weight:800;">💡 유사 모델 발견 (클릭 시 자동 완성)</span>', unsafe_allow_html=True)
                m_cols = st.columns(len(matches))
                for idx, m_name in enumerate(matches):
                    if m_cols[idx].button(f"📍 {m_name}", key=f"m_btn_{idx}", use_container_width=True):
                        st.session_state.prod_val = m_name; st.rerun()
        
        st.markdown('<div class="group-title">💰 금액 및 상세 할인 설정</div>', unsafe_allow_html=True)
        p_raw = st.text_input("정상가 (원)", value="", key="ad_praw")
        
        cd1, cd2 = st.columns(2)
        with cd1:
            cov = extract_num(st.text_input("쿠폰 할인", value="", key="ad_cov"))
            cot = st.radio("쿠폰 단위", ["원", "%"], horizontal=True, key="ad_cot")
            ex1v = extract_num(st.text_input("기타 할인 1", value="", key="ad_ex1v"))
            ex1t = st.radio("기타 1 단위", ["원", "%"], horizontal=True, key="ad_ex1t")
        with cd2:
            cav = extract_num(st.text_input("카드 할인", value="", key="ad_cav"))
            cat_unit = st.radio("카드 단위", ["원", "%"], horizontal=True, key="ad_catu")
            ex2v = extract_num(st.text_input("기타 할인 2", value="", key="ad_ex2v"))
            ex2t = st.radio("기타 2 단위", ["원", "%"], horizontal=True, key="ad_ex2t")
            
        gift = st.text_area("🎁 사은품 구성", key="ad_gift")
        
        p_v = extract_num(p_raw)
        d_coupon = cov if cot=="원" else p_v*(cov/100)
        d_card = cav if cat_unit=="원" else p_v*(cav/100)
        d_ex1 = ex1v if ex1t=="원" else p_v*(ex1v/100)
        d_ex2 = ex2v if ex2t=="원" else p_v*(ex2v/100)
        
        auto_f = int(p_v - d_coupon - d_card - d_ex1 - d_ex2)
        st.info(f"📋 자동 계산 혜택가 (쿠폰+카드+기타1,2 반영): {auto_f:,}원")
        
        feel_i = st.text_input("✨ 최종 체감가 (원)", value="", key="ad_fee")
        ev_date = st.date_input("행사 일정", [date.today(), date.today()], key="ad_date")
        
        if st.button("🚀 핫딜 데이터베이스 등록", use_container_width=True):
            if not prod: st.error("제품명을 입력하세요!")
            else:
                f_pf, f_br = pf_m if pf_m.strip() else pf_s, br_m if br_m.strip() else br_s
                dr = f"{ev_date[0]} ~ {ev_date[1]}" if len(ev_date)==2 else str(ev_date[0])
                new = pd.DataFrame([{"선택":False,"등록날짜":datetime.now().strftime("%Y-%m-%d"),"카테고리":cat,"플랫폼":f_pf,"브랜드":f_br,"제품명":prod,"표준모델명":std,"정상가":f"{int(p_v):,}원","행사일정":dr,"최종혜택가":f"{int(auto_f):,}원","체감가":f"{int(extract_num(feel_i)):,}원","사은품":gift}])
                pd.concat([db, new], ignore_index=True).to_csv(DB_PATH, index=False, encoding="utf-8-sig")
                st.session_state.prod_val = ""; st.success("등록 완료!"); time.sleep(1); st.cache_data.clear(); st.rerun()

    with t2:
        if not db.empty:
            ed = st.data_editor(db, use_container_width=True, hide_index=True, key="ad_editor")
            if st.button("💾 저장", use_container_width=True): ed.to_csv(DB_PATH, index=False, encoding="utf-8-sig"); st.cache_data.clear(); st.rerun()
            if st.button("🗑️ 삭제", use_container_width=True): ed[ed["선택"]==False].to_csv(DB_PATH, index=False, encoding="utf-8-sig"); st.cache_data.clear(); st.rerun()

    with t3:
        st.markdown('<div class="group-title">✍️ 새 게시물 등록</div>', unsafe_allow_html=True)
        with st.form("ad_nt", clear_on_submit=True):
            nt, tit, cont = st.radio("유형", ["공지사항", "업데이트"], horizontal=True), st.text_input("제목"), st.text_area("내용")
            if st.form_submit_button("📝 등록"):
                if tit and cont:
                    new_n = pd.DataFrame([{"선택":False,"날짜":date.today().strftime("%Y-%m-%d"),"유형":nt,"제목":tit,"내용":cont}])
                    pd.concat([ndb, new_n], ignore_index=True).to_csv(NOTICE_PATH, index=False, encoding="utf-8-sig")
                    st.success("등록 완료!"); st.cache_data.clear(); st.rerun()
        
        st.markdown('<div class="group-title">📝 기존 게시물 관리 (수정/삭제)</div>', unsafe_allow_html=True)
        if not ndb.empty:
            f_type = st.selectbox("관리할 유형 선택", ["전체", "공지사항", "업데이트"])
            manage_df = ndb.copy()
            if f_type != "전체": manage_df = manage_df[manage_df["유형"] == f_type]
            ed_ndb = st.data_editor(manage_df, use_container_width=True, hide_index=True, key="ndb_editor")
            ec1, ec2 = st.columns(2)
            if ec1.button("💾 게시물 수정 저장", use_container_width=True):
                if f_type == "전체": ed_ndb.to_csv(NOTICE_PATH, index=False, encoding="utf-8-sig")
                else:
                    other_df = ndb[ndb["유형"] != f_type]
                    pd.concat([other_df, ed_ndb], ignore_index=True).to_csv(NOTICE_PATH, index=False, encoding="utf-8-sig")
                st.success("수정 내용이 저장되었습니다."); st.cache_data.clear(); st.rerun()
            if ec2.button("🗑️ 선택 게시물 삭제", use_container_width=True):
                final_ndb = ed_ndb[ed_ndb["선택"] == False]
                if f_type != "전체":
                    other_df = ndb[ndb["유형"] != f_type]
                    final_ndb = pd.concat([other_df, final_ndb], ignore_index=True)
                final_ndb.to_csv(NOTICE_PATH, index=False, encoding="utf-8-sig")
                st.success("삭제 완료!"); st.cache_data.clear(); st.rerun()
        else:
            st.info("등록된 게시물이 없습니다.")