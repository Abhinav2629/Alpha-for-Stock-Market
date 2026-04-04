import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, date, timedelta

# --- 1. SETTINGS & AGGRESSIVE MOBILE CSS ---
st.set_page_config(layout="wide", page_title="Project Alpha v32.0", page_icon="🛡️")

st.markdown("""
    <style>
    [data-testid="stVerticalBlock"] > div { padding-top: 0.05rem; padding-bottom: 0.05rem; }
    hr { margin-top: 0.3rem !important; margin-bottom: 0.3rem !important; }
    [data-testid="stMetric"] { background-color: #262730 !important; padding: 15px !important; border-radius: 12px !important; border: 1px solid #41444C !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.8rem !important; font-weight: 700 !important; }

    /* MOBILE SIDE-SCROLL ENGINE */
    @media (max-width: 768px) {
        div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            padding-bottom: 15px !important;
        }
        div[data-testid="column"] {
            flex: 0 0 auto !important;
            width: auto !important;
            min-width: 90px !important;
            white-space: nowrap !important;
            margin-right: 15px !important;
        }
        div[data-testid="column"]:nth-child(1) { min-width: 130px !important; }
        div[data-testid="column"]:nth-child(9) { min-width: 450px !important; white-space: normal !important; }
    }
    .stock-name, .state-signal { font-size: 14px; font-weight: bold; white-space: nowrap !important; }
    .stInfo { padding: 12px !important; font-size: 13px !important; line-height: 1.5 !important; border-left: 5px solid #2e9aff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR & RISK PARAMETERS ---
st.sidebar.title("🛡️ Alpha Command")
total_capital, risk_amt, max_allocation = 200000, 2000, 20000

target_date = st.sidebar.date_input("Analysis Date", value=date.today())
cap_choice = st.sidebar.selectbox("Market Segment", ["Large Cap", "Mid Cap", "Small Cap"])
search_q = st.sidebar.text_input("🔍 Search Terminal", "").upper()
sl_mult = st.sidebar.slider("Volatility Buffer (SL Multiplier)", 1.0, 3.0, 1.5)
only_buys = st.sidebar.toggle("🔥 Show Actionable Alpha Only", value=False)

# --- 3. REPOSITORY ---
TICKER_MAP = {
    "Large Cap": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BHARTIARTL.NS", "SBIN.NS", "INFY.NS", "LICI.NS", "ITC.NS", "HUL.NS", "LT.NS", "BAJFINANCE.NS", "AXISBANK.NS", "KOTAKBANK.NS", "SUNPHARMA.NS", "ADANIENT.NS", "TATAMOTORS.NS", "MARUTI.NS", "NTPC.NS", "TITAN.NS", "ONGC.NS", "ADANIPORTS.NS", "POWERGRID.NS", "ASIANPAINT.NS", "HCLTECH.NS", "COALINDIA.NS", "TATASTEEL.NS", "BAJAJFINSV.NS", "ULTRACEMCO.NS", "M&M.NS", "JSWSTEEL.NS", "GRASIM.NS", "NESTLEIND.NS", "WIPRO.NS", "LTIM.NS", "HINDALCO.NS", "SBILIFE.NS", "BAJAJ-AUTO.NS", "ADANIGREEN.NS", "BEL.NS", "TATAELXSI.NS", "TRENT.NS", "VBL.NS", "SHRIRAMFIN.NS", "TATACONSUM.NS", "CIPLA.NS", "DRREDDY.NS", "BPCL.NS", "EICHERMOT.NS", "BRITANNIA.NS", "GAIL.NS", "INDIGO.NS", "HAL.NS", "ADANIPOWER.NS", "DLF.NS", "IOC.NS", "JINDALSTEL.NS", "CHOLAFIN.NS", "SIEMENS.NS", "TATACOMM.NS", "ABB.NS", "AMBUJACEM.NS", "BANKBARODA.NS", "BERGEPAINT.NS", "CANBK.NS", "COLPAL.NS", "DABUR.NS", "DIVISLAB.NS", "EXIDEIND.NS", "FEDERALBNK.NS", "GLAND.NS", "GODREJCP.NS", "HAVELLS.NS", "HEROMOTOCO.NS", "HINDZINC.NS", "ICICIPRULI.NS", "IDFCFIRSTB.NS", "INDUSINDBK.NS", "IRCTC.NS", "JSWENERGY.NS", "JUBLFOOD.NS", "LUPIN.NS", "MARICO.NS", "MCDOWELL-N.NS", "MUTHOOTFIN.NS", "NMDC.NS", "OBEROIRLTY.NS", "PIDILITIND.NS", "PNB.NS", "RECLTD.NS", "MOTHERSON.NS", "SHREECEM.NS", "SRF.NS", "TATACHEM.NS", "TATAPOWER.NS", "TVSMOTOR.NS", "UPL.NS", "VEDL.NS", "YESBANK.NS", "ZOMATO.NS", "JIOFIN.NS"],
    "Mid Cap": ["BSE.NS", "INDUSTOWER.NS", "POLYCAB.NS", "GMRINFRA.NS", "ASHOKLEY.NS", "BHEL.NS", "MAXHEALTH.NS", "PERSISTENT.NS", "MANKIND.NS", "BHARATFORG.NS", "OIL.NS", "AUROPHARMA.NS", "SWIGGY.NS", "NHPC.NS", "NYKAA.NS", "HPCL.NS", "POLICYBZR.NS", "AUBANK.NS", "NAUKRI.NS", "PAYTM.NS", "ALKEM.NS", "MCX.NS", "SBICCARD.NS", "DIXON.NS", "FORTIS.NS", "LAURUSLABS.NS", "PHOENIXLTD.NS", "APLAPOLLO.NS", "MAXFSL.NS", "TIINDIA.NS", "PRESTIGE.NS", "SUPREMEIND.NS", "GODREJPROP.NS", "MPHASIS.NS", "COFORGE.NS", "VOLTAS.NS", "CONCOR.NS", "CUMMINSIND.NS", "ESCORTS.NS", "GUJGASLTD.NS", "IDBI.NS", "IGL.NS", "INDIANB.NS", "IPCALAB.NS", "JKCEMENT.NS", "LICHSGFIN.NS", "LTTS.NS", "MRF.NS", "OFSS.NS", "PAGEIND.NS", "PETRONET.NS", "PFC.NS", "RAMCOCEM.NS", "RVNL.NS", "SYNGENE.NS", "UNIONBANK.NS", "WHIRLPOOL.NS", "ZEEL.NS", "ABFRL.NS", "ACC.NS", "AJANTPHARM.NS", "APOLLOTYRE.NS", "BALKRISIND.NS", "BANDHANBNK.NS", "BATAINDIA.NS", "BEL.NS", "BIOCON.NS", "COROMANDEL.NS", "CROMPTON.NS", "DEEPAKNTR.NS", "DELHIVERY.NS", "GLENMARK.NS", "IEX.NS", "INDHOTEL.NS", "L&TFH.NS", "ASTRAL.NS", "KEI.NS", "KPITTECH.NS", "MAZDOCK.NS", "SJVN.NS", "SUNTV.NS", "UNOMINDA.NS", "MANYAVAR.NS", "PATANJALI.NS", "MRPL.NS", "ARCHEAN.NS", "KAYNES.NS", "GODREJIND.NS", "CENTURYPLY.NS", "METROPOLIS.NS", "TATACOMM.NS", "UPL.NS"],
    "Small Cap": ["IREDA.NS", "HINDCOPPER.NS", "ASTERDM.NS", "NH.NS", "POONAWALLA.NS", "SONACOMS.NS", "NAVINFLUOR.NS", "ANANDRATHI.NS", "KARURVYSYA.NS", "HIMATSEIDE.NS", "NBCC.NS", "WELCORP.NS", "LALPATHLAB.NS", "AMBER.NS", "TATATECH.NS", "ANGELONE.NS", "MANAPPURAM.NS", "AEGISLOG.NS", "WOCKPHARMA.NS", "PNBHOUSING.NS", "CESC.NS", "AFFLE.NS", "PPLPHARMA.NS", "RBLBANK.NS", "IIFL.NS", "NATCOPHARM.NS", "CITYUNIONB.NS", "CAMS.NS", "FIVESTAR.NS", "INOXWIND.NS", "KEC.NS", "KFINTECH.NS", "PGELECTRO.NS", "REDINGTON.NS", "RPOWER.NS", "SUVENPHAR.NS", "ZENSARTECH.NS", "IRFC.NS", "HUDCO.NS", "PCJEWELLER.NS", "COCHINSHIP.NS", "GRSE.NS", "GOKEX.NS", "SWANENERGY.NS", "TEJASNET.NS", "HFCL.NS", "ITI.NS", "RAILTEL.NS", "GPIL.NS", "TIRUMALCHM.NS", "KOPRAN.NS", "MOREPENLAB.NS", "MARKSANS.NS", "SMSPHARMA.NS", "AARTIDRUGS.NS", "GRANULES.NS", "ERIS.NS", "PFIZER.NS", "JBCHEPHARM.NS", "SANWS.NS", "HINDWARE.NS", "CERA.NS", "KAJARIACER.NS", "SOMANYCERA.NS", "SUNTECK.NS", "PURVA.NS", "MAHLIFE.NS", "BRIGADE.NS", "SOBHA.NS", "EASEMYTRIP.NS", "BLS.NS", "THOMASCOOK.NS", "VIPIND.NS", "SYMPHONY.NS", "EUREKAFORBE.NS", "ORIENTBELL.NS", "BORORENEW.NS", "GENUSPOWER.NS", "HPL.NS", "BOROSIL.NS", "LAOPALA.NS", "KIRLFERROS.NS", "THANGAMAYL.NS", "INOXINDIA.NS", "JWL.NS", "TITAGARH.NS", "SIGNATURE.NS", "HAPPYFORG.NS", "KIRLOSENG.NS", "RAMRAT.NS"]
}

# --- 4. ENGINE ---
@st.cache_data(ttl=600)
def fetch_cloud_data(tickers, mode, analysis_date):
    try:
        p_map = {"Day Trading": "1mo", "Swing Trading": "6mo", "Positional": "2y", "Investors": "5y"}
        i_map = {"Day Trading": "5m", "Swing Trading": "1h", "Positional": "1d", "Investors": "1wk"}
        return yf.download(tickers, period=p_map[mode], interval=i_map[mode], group_by='ticker', auto_adjust=True, progress=False)
    except: return None

def analyze_v32(df, risk_val, alloc_val, mult, analysis_date):
    try:
        df = df[df.index <= analysis_date.strftime('%Y-%m-%d')]
        if df.empty or len(df) < 25: return None
        hi_52, lo_52 = float(df.last('365D')['High'].max()), float(df.last('365D')['Low'].min())
        df['RSI'], df['EMA20'], df['EMA200'], df['ATR'] = ta.rsi(df['Close'], length=14), ta.ema(df['Close'], length=20), ta.ema(df['Close'], length=200), ta.atr(df['High'], df['Low'], df['Close'], length=14)
        lp, rsi, ema20 = float(df['Close'].iloc[-1]), df['RSI'].iloc[-1], df['EMA20'].iloc[-1]
        sl = round(lp - (mult * df['ATR'].iloc[-1]), 2)
        qty = min(int(risk_val / (lp - sl)), int(alloc_val / lp)) if lp > sl else 0
        gc = ema20 > df['EMA200'].iloc[-1] if not df['EMA200'].isnull().all() else False
        state = "BUY" if rsi > 55 else "WAIT" if rsi > df['RSI'].iloc[-2] else "NEUTRAL" if 45 <= rsi <= 55 else "SELL"
        mtf = 60 + (20 if lp > ema20 else 0) + (20 if rsi > 55 else 0)
        gc_note = "🌟 GC Floor active." if gc else "🌑 No GC support."
        pov = f"**{state}** trigger (RSI: {rsi:.1f}). MTF: {mtf}%. {gc_note}"
        return {"price": lp, "hi52": hi_52, "lo52": lo_52, "mtf": mtf, "state": state, "sl": sl, "qty": qty, "pov": pov}
    except: return None

# --- 5. RENDERER ---
m_indices = {"Nifty 50": "^NSEI", "Bank Nifty": "^NSEBANK", "Nifty IT": "^CNXIT"}
m_cols = st.columns(4) 
for i, (n, t) in enumerate(m_indices.items()):
    try:
        d = yf.Ticker(t).history(period="5d")
        m_cols[i].metric(n, f"{d['Close'].iloc[-1]:,.0f}", f"{((d['Close'].iloc[-1]-d['Close'].iloc[-2])/d['Close'].iloc[-2])*100:.2f}%")
    except: pass
m_cols[3].metric("Terminal Status", "ONLINE", "Synced")

st.divider()
current_list = [t for t in TICKER_MAP[cap_choice] if search_q in t]
tabs = st.tabs(["Day Trading", "Swing Trading", "Positional", "Investors"])

for tab_idx, mode in enumerate(["Day Trading", "Swing Trading", "Positional", "Investors"]):
    with tabs[tab_idx]:
        bulk_data = fetch_cloud_data(current_list, mode, target_date)
        if bulk_data is None: 
            st.error("Market Data Synchronizer failed. Please check connection.")
            continue
        h = st.columns([1.2, 0.6, 1, 1, 1, 1, 1, 1.8, 4.5, 1.5])
        h[0].write("**Stock**"); h[1].write("**Chart**"); h[2].write("**Price**"); h[3].write("**52W High**"); h[4].write("**52W Low**")
        h[5].write("**State**"); h[6].write("**Strength**"); h[7].write("**Smart Stake**"); h[8].write("**Professional POV**"); h[9].write("**Action**")
        st.divider()

        for i, symbol in enumerate(current_list):
            data = analyze_v32(bulk_data[symbol] if len(current_list) > 1 else bulk_data, risk_amt, max_allocation, sl_mult, target_date)
            if data:
                status = st.session_state.get(f"v32_{mode}_{i}", "-")
                if status == "Bought": sig, col = ("HOLD", "blue") if data['mtf'] > 45 else ("CLOSE", "red")
                else: sig = data['state']; col = "cyan" if sig == "WAIT" else "gray" if sig == "NEUTRAL" else "green" if sig == "BUY" else "red"
                if only_buys and sig not in ["BUY", "WAIT", "HOLD"]: continue
                c = st.columns([1.2, 0.6, 1, 1, 1, 1, 1, 1.8, 4.5, 1.5])
                c[0].markdown(f"<span class='stock-name'>{symbol.replace('.NS','')}</span>", unsafe_allow_html=True)
                c[1].link_button("📊", f"https://www.tradingview.com/chart/?symbol=NSE:{symbol.replace('.NS','')}")
                c[2].write(f"₹{data['price']:,.1f}"); c[3].write(f"₹{data['hi52']:,.1f}"); c[4].write(f"₹{data['lo52']:,.1f}")
                c[5].markdown(f"<span class='state-signal' style='color:{col}'>{sig}</span>", unsafe_allow_html=True); c[6].progress(int(data['mtf']))
                with c[7]: st.caption(f"Exit: ₹{data['sl']}"); st.write(f"**Qty: {data['qty']}**")
                c[8].info(data['pov'])
                res = c[9].selectbox("Position", ["-", "Bought", "Sold"], key=f"sel32_{mode}_{i}")
                st.session_state[f"v32_{mode}_{i}"] = res
                st.divider()
