import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, date

# --- 1. SETTINGS & CSS (FROZEN FROM v25) ---
st.set_page_config(layout="wide", page_title="Project Alpha v26.0", page_icon="🛡️")

st.markdown("""
    <style>
    [data-testid="stVerticalBlock"] > div { padding-top: 0.05rem; padding-bottom: 0.05rem; }
    hr { margin-top: 0.3rem !important; margin-bottom: 0.3rem !important; }
    [data-testid="stMetric"] {
        background-color: #262730 !important;
        padding: 15px !important;
        border-radius: 12px !important;
        border: 1px solid #41444C !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3) !important;
    }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.8rem !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { color: #BDC3C7 !important; font-size: 1rem !important; }
    .stock-name, .state-signal { font-size: 14px; font-weight: bold; }
    .stInfo { padding: 12px !important; font-size: 13px !important; line-height: 1.5 !important; border-left: 5px solid #2e9aff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR: THE PORTFOLIO RISK CENTER (FROZEN) ---
st.sidebar.title("🛡️ Portfolio Command")
total_capital = 200000
risk_amt = 2000 
max_allocation = 20000

st.sidebar.metric("Account Risk Unit", f"₹{risk_amt:,.0f}")
st.sidebar.caption(f"Strategy: Fixed 1% Risk | Max ₹20k Exposure")

cap_choice = st.sidebar.selectbox("Market Segment", ["Large Cap", "Mid Cap", "Small Cap"])
search_q = st.sidebar.text_input("🔍 Search Terminal", "").upper()
sl_mult = st.sidebar.slider("Volatility Buffer (SL Multiplier)", 1.0, 3.0, 1.5)
only_buys = st.sidebar.toggle("🔥 Show Actionable Alpha Only", value=False)

# --- 3. REPOSITORY (TOP 100 PER HEAD) ---
TICKER_MAP = {
    "Large Cap": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BHARTIARTL.NS", "SBIN.NS", "INFY.NS", "LICI.NS", "ITC.NS", "HUL.NS", "LT.NS", "BAJFINANCE.NS", "AXISBANK.NS", "KOTAKBANK.NS", "SUNPHARMA.NS", "ADANIENT.NS", "TATAMOTORS.NS", "MARUTI.NS", "NTPC.NS", "TITAN.NS", "ONGC.NS", "ADANIPORTS.NS", "POWERGRID.NS", "ASIANPAINT.NS", "HCLTECH.NS", "COALINDIA.NS", "TATASTEEL.NS", "BAJAJFINSV.NS", "ULTRACEMCO.NS", "M&M.NS", "JSWSTEEL.NS", "GRASIM.NS", "NESTLEIND.NS", "WIPRO.NS", "LTIM.NS", "HINDALCO.NS", "SBILIFE.NS", "BAJAJ-AUTO.NS", "ADANIGREEN.NS", "BEL.NS", "TATAELXSI.NS", "TRENT.NS", "VBL.NS", "SHRIRAMFIN.NS", "TATACONSUM.NS", "CIPLA.NS", "DRREDDY.NS", "BPCL.NS", "EICHERMOT.NS", "BRITANNIA.NS", "GAIL.NS", "INDIGO.NS", "HAL.NS", "ADANIPOWER.NS", "DLF.NS", "IOC.NS", "JINDALSTEL.NS", "CHOLAFIN.NS", "SIEMENS.NS", "TATACOMM.NS", "ABB.NS", "AMBUJACEM.NS", "BANKBARODA.NS", "BERGEPAINT.NS", "CANBK.NS", "COLPAL.NS", "DABUR.NS", "DIVISLAB.NS", "EXIDEIND.NS", "FEDERALBNK.NS", "GLAND.NS", "GODREJCP.NS", "HAVELLS.NS", "HEROMOTOCO.NS", "HINDZINC.NS", "ICICIPRULI.NS", "IDFCFIRSTB.NS", "INDUSINDBK.NS", "IRCTC.NS", "JSWENERGY.NS", "JUBLFOOD.NS", "LUPIN.NS", "MARICO.NS", "MCDOWELL-N.NS", "MUTHOOTFIN.NS", "NMDC.NS", "OBEROIRLTY.NS", "PIDILITIND.NS", "PNB.NS", "RECLTD.NS", "MOTHERSON.NS", "SHREECEM.NS", "SRF.NS", "TATACHEM.NS", "TATAPOWER.NS", "TVSMOTOR.NS", "UPL.NS", "VEDL.NS", "YESBANK.NS", "ZOMATO.NS", "JIOFIN.NS"],
    "Mid Cap": ["BSE.NS", "INDUSTOWER.NS", "POLYCAB.NS", "GMRINFRA.NS", "ASHOKLEY.NS", "BHEL.NS", "MAXHEALTH.NS", "PERSISTENT.NS", "MANKIND.NS", "BHARATFORG.NS", "OIL.NS", "AUROPHARMA.NS", "SWIGGY.NS", "NHPC.NS", "NYKAA.NS", "HPCL.NS", "POLICYBZR.NS", "AUBANK.NS", "NAUKRI.NS", "PAYTM.NS", "ALKEM.NS", "MCX.NS", "SBICARD.NS", "DIXON.NS", "FORTIS.NS", "LAURUSLABS.NS", "PHOENIXLTD.NS", "APLAPOLLO.NS", "MAXFSL.NS", "TIINDIA.NS", "PRESTIGE.NS", "SUPREMEIND.NS", "GODREJPROP.NS", "MPHASIS.NS", "COFORGE.NS", "VOLTAS.NS", "CONCOR.NS", "CUMMINSIND.NS", "ESCORTS.NS", "GUJGASLTD.NS", "IDBI.NS", "IGL.NS", "INDIANB.NS", "IPCALAB.NS", "JKCEMENT.NS", "LICHSGFIN.NS", "LTTS.NS", "MRF.NS", "OFSS.NS", "PAGEIND.NS", "PETRONET.NS", "PFC.NS", "RAMCOCEM.NS", "RVNL.NS", "SYNGENE.NS", "UNIONBANK.NS", "WHIRLPOOL.NS", "ZEEL.NS", "ABFRL.NS", "ACC.NS", "AJANTPHARM.NS", "APOLLOTYRE.NS", "BALKRISIND.NS", "BANDHANBNK.NS", "BATAINDIA.NS", "BEL.NS", "BIOCON.NS", "COROMANDEL.NS", "CROMPTON.NS", "DEEPAKNTR.NS", "DELHIVERY.NS", "GLENMARK.NS", "IEX.NS", "INDHOTEL.NS", "L&TFH.NS", "ASTRAL.NS", "KEI.NS", "KPITTECH.NS", "MAZDOCK.NS", "SJVN.NS", "SUNTV.NS", "UNOMINDA.NS", "MANYAVAR.NS", "PATANJALI.NS", "MRPL.NS", "ARCHEAN.NS", "KAYNES.NS", "GODREJIND.NS", "CENTURYPLY.NS", "METROPOLIS.NS", "TATACOMM.NS", "UPL.NS"],
    "Small Cap": ["IREDA.NS", "HINDCOPPER.NS", "ASTERDM.NS", "NH.NS", "POONAWALLA.NS", "SONACOMS.NS", "NAVINFLUOR.NS", "ANANDRATHI.NS", "KARURVYSYA.NS", "HIMATSEIDE.NS", "NBCC.NS", "WELCORP.NS", "LALPATHLAB.NS", "AMBER.NS", "TATATECH.NS", "ANGELONE.NS", "MANAPPURAM.NS", "AEGISLOG.NS", "WOCKPHARMA.NS", "PNBHOUSING.NS", "CESC.NS", "AFFLE.NS", "PPLPHARMA.NS", "RBLBANK.NS", "IIFL.NS", "NATCOPHARM.NS", "CITYUNIONB.NS", "CAMS.NS", "FIVESTAR.NS", "INOXWIND.NS", "KEC.NS", "KFINTECH.NS", "PGELECTRO.NS", "REDINGTON.NS", "RPOWER.NS", "SUVENPHAR.NS", "ZENSARTECH.NS", "IRFC.NS", "HUDCO.NS", "PCJEWELLER.NS", "COCHINSHIP.NS", "GRSE.NS", "GOKEX.NS", "SWANENERGY.NS", "TEJASNET.NS", "HFCL.NS", "ITI.NS", "RAILTEL.NS", "GPIL.NS", "TIRUMALCHM.NS", "KOPRAN.NS", "MOREPENLAB.NS", "MARKSANS.NS", "SMSPHARMA.NS", "AARTIDRUGS.NS", "GRANULES.NS", "ERIS.NS", "PFIZER.NS", "JBCHEPHARM.NS", "SANWS.NS", "HINDWARE.NS", "CERA.NS", "KAJARIACER.NS", "SOMANYCERA.NS", "SUNTECK.NS", "PURVA.NS", "MAHLIFE.NS", "BRIGADE.NS", "SOBHA.NS", "EASEMYTRIP.NS", "BLS.NS", "THOMASCOOK.NS", "VIPIND.NS", "SYMPHONY.NS", "EUREKAFORBE.NS", "ORIENTBELL.NS", "BORORENEW.NS", "GENUSPOWER.NS", "HPL.NS", "BOROSIL.NS", "LAOPALA.NS", "KIRLFERROS.NS", "THANGAMAYL.NS", "INOXINDIA.NS", "JWL.NS", "TITAGARH.NS", "SIGNATURE.NS", "HAPPYFORG.NS", "KIRLOSENG.NS", "RAMRAT.NS"]
}

# --- 4. DATA & NARRATIVE ENGINE (POINT 2: MTF INCLUDED) ---
@st.cache_data(ttl=600)
def fetch_bulk_clean_v26(tickers, mode):
    p_map = {"Day Trading": "5d", "Swing Trading": "2mo", "Positional": "1y", "Investors": "3y"}
    i_map = {"Day Trading": "5m", "Swing Trading": "1h", "Positional": "1d", "Investors": "1wk"}
    return yf.download(tickers, period=p_map[mode], interval=i_map[mode], group_by='ticker', auto_adjust=True, progress=False)

def analyze_v26(df, risk_val, alloc_val, mult):
    try:
        if df.empty or len(df) < 25: return None
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['EMA200'] = ta.ema(df['Close'], length=200)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        lp, rsi, prsi = float(df['Close'].iloc[-1]), df['RSI'].iloc[-1], df['RSI'].iloc[-2]
        atr = df['ATR'].iloc[-1]
        
        # Risk Math
        sl = round(lp - (mult * atr), 2)
        qty = min(int(risk_val / (lp - sl)), int(alloc_val / lp)) if lp > sl else 0
        gc = df['EMA20'].iloc[-1] > df['EMA200'].iloc[-1] if not df['EMA200'].isnull().all() else False
        state = "BUY" if rsi > 55 else "WAIT" if rsi > prsi else "NEUTRAL" if 45 <= rsi <= 55 else "SELL"
        
        # POINT 2: MTF Score Logic (Agreement between EMA and RSI)
        mtf_score = 60 # Base
        if lp > df['EMA20'].iloc[-1]: mtf_score += 20
        if rsi > 55: mtf_score += 20
        
        gc_note = "🌟 Structural Floor: Golden Cross active." if gc else "🌑 Structural Weakness: No GC support."
        
        pov = f"**ANALYSIS:** {state} trigger based on RSI {rsi:.1f}. Price is {'holding' if lp > df['EMA20'].iloc[-1] else 'failing'} at the 20-EMA. **MTF Confluence: {mtf_score}%**. {gc_note}"
        
        return {"price": lp, "conf": mtf_score, "state": state, "sl": sl, "qty": qty, "gc": gc, "pov": pov}
    except: return None

# --- 5. DASHBOARD RENDERER ---
# POINT 1: SEGMENT MOMENTUM CALCULATION
m_indices = {"Nifty 50": "^NSEI", "Bank Nifty": "^NSEBANK", "Nifty IT": "^CNXIT"}
m_cols = st.columns(4) # Added 4th Column
for i, (name, ticker) in enumerate(m_indices.items()):
    try:
        d = yf.Ticker(ticker).history(period="5d")
        chg = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
        m_cols[i].metric(name, f"{d['Close'].iloc[-1]:,.0f}", f"{chg:.2f}%")
    except: pass

# Segment Header Metric
m_cols[3].metric("Segment Momentum", f"{cap_choice}", "Analyzing...")

st.divider()

current_list = [t for t in TICKER_MAP[cap_choice] if search_q in t]
tabs = st.tabs(["Day Trading", "Swing Trading", "Positional", "Investors"])

for tab_idx, mode in enumerate(["Day Trading", "Swing Trading", "Positional", "Investors"]):
    with tabs[tab_idx]:
        with st.spinner(f"Updating {mode} Engine..."):
            bulk_data = fetch_bulk_clean_v26(current_list, mode)
        
        h = st.columns([1.2, 0.6, 1, 1, 1.2, 1.8, 4.5, 1.5])
        h[0].write("**Stock**"); h[1].write("**Chart**"); h[2].write("**Price**"); h[3].write("**State**")
        h[4].write("**Strength**"); h[5].write("**Smart Stake**"); h[6].write("**Professional Analyst POV**"); h[7].write("**Action**")
        st.divider()

        buy_count = 0
        for i, symbol in enumerate(current_list):
            try:
                ticker_df = bulk_data[symbol] if len(current_list) > 1 else bulk_data
                data = analyze_v26(ticker_df, risk_amt, max_allocation, sl_mult)
            except: data = None
            
            if data:
                if data['state'] == "BUY": buy_count += 1
                status = st.session_state.get(f"v26_{mode}_{i}", "-")
                if status == "Bought": sig, col = ("HOLD", "blue") if data['conf'] > 45 else ("CLOSE", "red")
                else: sig = data['state']; col = "cyan" if sig == "WAIT" else "gray" if sig == "NEUTRAL" else "green" if sig == "BUY" else "red"
                
                if only_buys and sig not in ["BUY", "WAIT", "HOLD"]: continue

                c = st.columns([1.2, 0.6, 1, 1, 1.2, 1.8, 4.5, 1.5])
                c[0].markdown(f"<span class='stock-name'>{symbol.replace('.NS','')}</span>", unsafe_allow_html=True)
                c[1].link_button("📊", f"https://www.tradingview.com/chart/?symbol=NSE:{symbol.replace('.NS','')}")
                c[2].write(f"₹{data['price']:,.2f}")
                c[3].markdown(f"<span class='state-signal' style='color:{col}'>{sig}</span>", unsafe_allow_html=True)
                c[4].progress(int(data['conf']))
                
                with c[5]:
                    st.caption(f"Exit: ₹{data['sl']}")
                    st.write(f"**Qty: {data['qty']}**")
                    st.caption(f"Risk: ₹{risk_amt}")
                
                c[6].info(data['pov'])
                
                res = c[7].selectbox("Position", ["-", "Bought", "Sold"], key=f"sel26_{mode}_{i}")
                st.session_state[f"v26_{mode}_{i}"] = res
                st.divider()
        
        # Update Segment Momentum card
        momentum_pct = (buy_count / len(current_list)) * 100 if current_list else 0
        st.toast(f"Sector Breadth: {momentum_pct:.1f}% of {cap_choice} is Bullish.")
