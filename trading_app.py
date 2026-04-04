import warnings
import sys
import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, date, timedelta

# --- SYSTEM ANCHOR ---
sys.modules['warnings'] = warnings 

# --- 1. SETTINGS & CSS (NO-WRAP ENFORCED) ---
st.set_page_config(layout="wide", page_title="Project Alpha v30.0", page_icon="🛡️")

st.markdown("""
    <style>
    /* Global Spacing */
    [data-testid="stVerticalBlock"] > div { padding-top: 0.05rem; padding-bottom: 0.05rem; }
    hr { margin-top: 0.3rem !important; margin-bottom: 0.3rem !important; }
    
    /* High-Contrast Metric Cards */
    [data-testid="stMetric"] {
        background-color: #262730 !important;
        padding: 15px !important;
        border-radius: 12px !important;
        border: 1px solid #41444C !important;
    }
    
    /* THE MOBILE SCROLL ENGINE */
    @media (max-width: 768px) {
        /* Force the row to never wrap and allow side-scrolling */
        div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            padding-bottom: 15px !important;
            align-items: flex-start !important;
        }
        
        /* Stop the columns from shrinking and force them to stay in one line */
        div[data-testid="column"] {
            flex: 0 0 auto !important;
            width: auto !important;
            min-width: 100px !important;
            white-space: nowrap !important; /* CRITICAL: Prevents RELIA-NCE stacking */
            margin-right: 20px !important;
        }
        
        /* Stock Name Column - slightly wider for long names */
        div[data-testid="column"]:nth-child(1) {
            min-width: 140px !important;
        }
        
        /* Detailed POV Column - Keep it wide but allow text to wrap INSIDE it */
        div[data-testid="column"]:nth-child(7) {
            min-width: 480px !important;
            white-space: normal !important;
        }

        /* Prevent buttons and boxes from squishing */
        .stSelectbox, .stButton, .stLinkButton {
            min-width: 120px !important;
        }
    }

    /* Enforce no-wrap on specific labels */
    .stock-name, .state-signal, [data-testid="stMetricValue"] { 
        white-space: nowrap !important; 
        font-size: 14px; 
        font-weight: bold; 
    }

    .stInfo { padding: 12px !important; font-size: 13px !important; line-height: 1.5 !important; border-left: 5px solid #2e9aff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR (FROZEN LOGIC) ---
st.sidebar.title("🛡️ Alpha Command")
total_capital, risk_amt, max_allocation = 200000, 2000, 20000

st.sidebar.subheader("📅 Analysis Timeline")
target_date = st.sidebar.date_input("Analysis Date", value=date.today(), max_value=date.today())

st.sidebar.subheader("⚙️ Portfolio Filters")
cap_choice = st.sidebar.selectbox("Market Segment", ["Large Cap", "Mid Cap", "Small Cap"])
search_q = st.sidebar.text_input("🔍 Search Terminal", "").upper()
sl_mult = st.sidebar.slider("Volatility Buffer (SL Multiplier)", 1.0, 3.0, 1.5)
only_buys = st.sidebar.toggle("🔥 Show Actionable Alpha Only", value=False)

# --- 3. REPOSITORY ---
TICKER_MAP = {
    "Large Cap": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BHARTIARTL.NS", "SBIN.NS", "INFY.NS", "LICI.NS", "ITC.NS", "HUL.NS", "LT.NS", "BAJFINANCE.NS", "AXISBANK.NS", "KOTAKBANK.NS", "SUNPHARMA.NS", "ADANIENT.NS", "TATAMOTORS.NS", "MARUTI.NS", "NTPC.NS", "TITAN.NS", "ONGC.NS", "ADANIPORTS.NS", "POWERGRID.NS", "ASIANPAINT.NS", "HCLTECH.NS", "COALINDIA.NS", "TATASTEEL.NS", "BAJAJFINSV.NS", "ULTRACEMCO.NS", "M&M.NS", "JSWSTEEL.NS", "GRASIM.NS", "NESTLEIND.NS", "WIPRO.NS", "LTIM.NS", "HINDALCO.NS", "SBILIFE.NS", "BAJAJ-AUTO.NS", "ADANIGREEN.NS", "BEL.NS", "TATAELXSI.NS", "TRENT.NS", "VBL.NS", "SHRIRAMFIN.NS", "TATACONSUM.NS", "CIPLA.NS", "DRREDDY.NS", "BPCL.NS", "EICHERMOT.NS", "BRITANNIA.NS", "GAIL.NS", "INDIGO.NS", "HAL.NS", "ADANIPOWER.NS", "DLF.NS", "IOC.NS", "JINDALSTEL.NS", "CHOLAFIN.NS", "SIEMENS.NS", "TATACOMM.NS", "ABB.NS", "AMBUJACEM.NS", "BANKBARODA.NS", "BERGEPAINT.NS", "CANBK.NS", "COLPAL.NS", "DABUR.NS", "DIVISLAB.NS", "EXIDEIND.NS", "FEDERALBNK.NS", "GLAND.NS", "GODREJCP.NS", "HAVELLS.NS", "HEROMOTOCO.NS", "HINDZINC.NS", "ICICIPRULI.NS", "IDFCFIRSTB.NS", "INDUSINDBK.NS", "IRCTC.NS", "JSWENERGY.NS", "JUBLFOOD.NS", "LUPIN.NS", "MARICO.NS", "MCDOWELL-N.NS", "MUTHOOTFIN.NS", "NMDC.NS", "OBEROIRLTY.NS", "PIDILITIND.NS", "PNB.NS", "RECLTD.NS", "MOTHERSON.NS", "SHREECEM.NS", "SRF.NS", "TATACHEM.NS", "TATAPOWER.NS", "TVSMOTOR.NS", "UPL.NS", "VEDL.NS", "YESBANK.NS", "ZOMATO.NS", "JIOFIN.NS"],
    "Mid Cap": ["BSE.NS", "INDUSTOWER.NS", "POLYCAB.NS", "GMRINFRA.NS", "ASHOKLEY.NS", "BHEL.NS", "MAXHEALTH.NS", "PERSISTENT.NS", "MANKIND.NS", "BHARATFORG.NS", "OIL.NS", "AUROPHARMA.NS", "SWIGGY.NS", "NHPC.NS", "NYKAA.NS", "HPCL.NS", "POLICYBZR.NS", "AUBANK.NS", "NAUKRI.NS", "PAYTM.NS", "ALKEM.NS", "MCX.NS", "SBICARD.NS", "DIXON.NS", "FORTIS.NS", "LAURUSLABS.NS", "PHOENIXLTD.NS", "APLAPOLLO.NS", "MAXFSL.NS", "TIINDIA.NS", "PRESTIGE.NS", "SUPREMEIND.NS", "GODREJPROP.NS", "MPHASIS.NS", "COFORGE.NS", "VOLTAS.NS", "CONCOR.NS", "CUMMINSIND.NS", "ESCORTS.NS", "GUJGASLTD.NS", "IDBI.NS", "IGL.NS", "INDIANB.NS", "IPCALAB.NS", "JKCEMENT.NS", "LICHSGFIN.NS", "LTTS.NS", "MRF.NS", "OFSS.NS", "PAGEIND.NS", "PETRONET.NS", "PFC.NS", "RAMCOCEM.NS", "RVNL.NS", "SYNGENE.NS", "UNIONBANK.NS", "WHIRLPOOL.NS", "ZEEL.NS", "ABFRL.NS", "ACC.NS", "AJANTPHARM.NS", "APOLLOTYRE.NS", "BALKRISIND.NS", "BANDHANBNK.NS", "BATAINDIA.NS", "BEL.NS", "BIOCON.NS", "COROMANDEL.NS", "CROMPTON.NS", "DEEPAKNTR.NS", "DELHIVERY.NS", "GLENMARK.NS", "IEX.NS", "INDHOTEL.NS", "L&TFH.NS", "ASTRAL.NS", "KEI.NS", "KPITTECH.NS", "MAZDOCK.NS", "SJVN.NS", "SUNTV.NS", "UNOMINDA.NS", "MANYAVAR.NS", "PATANJALI.NS", "MRPL.NS", "ARCHEAN.NS", "KAYNES.NS", "GODREJIND.NS", "CENTURYPLY.NS", "METROPOLIS.NS", "TATACOMM.NS", "UPL.NS"],
    "Small Cap": ["IREDA.NS", "HINDCOPPER.NS", "ASTERDM.NS", "NH.NS", "POONAWALLA.NS", "SONACOMS.NS", "NAVINFLUOR.NS", "ANANDRATHI.NS", "KARURVYSYA.NS", "HIMATSEIDE.NS", "NBCC.NS", "WELCORP.NS", "LALPATHLAB.NS", "AMBER.NS", "TATATECH.NS", "ANGELONE.NS", "MANAPPURAM.NS", "AEGISLOG.NS", "WOCKPHARMA.NS", "PNBHOUSING.NS", "CESC.NS", "AFFLE.NS", "PPLPHARMA.NS", "RBLBANK.NS", "IIFL.NS", "NATCOPHARM.NS", "CITYUNIONB.NS", "CAMS.NS", "FIVESTAR.NS", "INOXWIND.NS", "KEC.NS", "KFINTECH.NS", "PGELECTRO.NS", "REDINGTON.NS", "RPOWER.NS", "SUVENPHAR.NS", "ZENSARTECH.NS", "IRFC.NS", "HUDCO.NS", "PCJEWELLER.NS", "COCHINSHIP.NS", "GRSE.NS", "GOKEX.NS", "SWANENERGY.NS", "TEJASNET.NS", "HFCL.NS", "ITI.NS", "RAILTEL.NS", "GPIL.NS", "TIRUMALCHM.NS", "KOPRAN.NS", "MOREPENLAB.NS", "MARKSANS.NS", "SMSPHARMA.NS", "AARTIDRUGS.NS", "GRANULES.NS", "ERIS.NS", "PFIZER.NS", "JBCHEPHARM.NS", "SANWS.NS", "HINDWARE.NS", "CERA.NS", "KAJARIACER.NS", "SOMANYCERA.NS", "SUNTECK.NS", "PURVA.NS", "MAHLIFE.NS", "BRIGADE.NS", "SOBHA.NS", "EASEMYTRIP.NS", "BLS.NS", "THOMASCOOK.NS", "VIPIND.NS", "SYMPHONY.NS", "EUREKAFORBE.NS", "ORIENTBELL.NS", "BORORENEW.NS", "GENUSPOWER.NS", "HPL.NS", "BOROSIL.NS", "LAOPALA.NS", "KIRLFERROS.NS", "THANGAMAYL.NS", "INOXINDIA.NS", "JWL.NS", "TITAGARH.NS", "SIGNATURE.NS", "HAPPYFORG.NS", "KIRLOSENG.NS", "RAMRAT.NS"]
}

# --- 4. ENGINE ---
def generate_elaborated_note(df, state, gc, rsi, lp, ema20):
    gc_status = "🌟 GC Active: Floor exists." if gc else "🌑 No GC: Resistance ahead."
    if state == "BUY":
        note = f"**BULLISH IGNITION:** Asset in 'High Velocity'. Above 20-EMA. RSI: {rsi:.1f}. {gc_status}"
    elif state == "WAIT":
        note = f"**RECOVERY ALERT:** RSI ({rsi:.1f}) curling from oversold. Monitoring close above EMA20 for 1:3 R/R setup. {gc_status}"
    elif state == "NEUTRAL":
        note = f"**EQUILIBRIUM:** Price hugging EMA20. Low commitment. RSI ({rsi:.1f}). Wait for expansion. {gc_status}"
    else:
        note = f"**BEARISH DOMINANCE:** Structural compromise. Downside liquidity hunting likely. RSI: {rsi:.1f}. {gc_status}"
    return note

@st.cache_data(ttl=600)
def fetch_alpha_data_v30(tickers, mode, analysis_date):
    p_map = {"Day Trading": "1mo", "Swing Trading": "6mo", "Positional": "2y", "Investors": "5y"}
    i_map = {"Day Trading": "5m", "Swing Trading": "1h", "Positional": "1d", "Investors": "1wk"}
    return yf.download(tickers, period=p_map[mode], interval=i_map[mode], group_by='ticker', auto_adjust=True, progress=False)

def analyze_v30(df, risk_val, alloc_val, mult, analysis_date):
    try:
        df = df[df.index <= analysis_date.strftime('%Y-%m-%d')]
        if df.empty or len(df) < 25: return None
        df['RSI'], df['EMA20'], df['EMA200'], df['ATR'] = ta.rsi(df['Close'], length=14), ta.ema(df['Close'], length=20), ta.ema(df['Close'], length=200), ta.atr(df['High'], df['Low'], df['Close'], length=14)
        lp, rsi, ema20 = float(df['Close'].iloc[-1]), df['RSI'].iloc[-1], df['EMA20'].iloc[-1]
        sl = round(lp - (mult * df['ATR'].iloc[-1]), 2)
        qty = min(int(risk_val / (lp - sl)), int(alloc_val / lp)) if lp > sl else 0
        gc = ema20 > df['EMA200'].iloc[-1] if not df['EMA200'].isnull().all() else False
        state = "BUY" if rsi > 55 else "WAIT" if rsi > df['RSI'].iloc[-2] else "NEUTRAL" if 45 <= rsi <= 55 else "SELL"
        mtf = 60 + (20 if lp > ema20 else 0) + (20 if rsi > 55 else 0)
        return {"price": lp, "mtf": mtf, "state": state, "sl": sl, "qty": qty, "pov": generate_elaborated_note(df, state, gc, rsi, lp, ema20)}
    except: return None

# --- 5. RENDERER ---
m_indices = {"Nifty 50": "^NSEI", "Bank Nifty": "^NSEBANK", "Nifty IT": "^CNXIT"}
m_cols = st.columns(4) 
for i, (name, ticker) in enumerate(m_indices.items()):
    try:
        d = yf.Ticker(ticker).history(period="5d")
        chg = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
        m_cols[i].metric(name, f"{d['Close'].iloc[-1]:,.0f}", f"{chg:.2f}%")
    except: pass
m_cols[3].metric("Segment Momentum", f"{cap_choice}", "Scanning...")

st.divider()

current_list = [t for t in TICKER_MAP[cap_choice] if search_q in t]
tabs = st.tabs(["Day Trading", "Swing Trading", "Positional", "Investors"])

for tab_idx, mode in enumerate(["Day Trading", "Swing Trading", "Positional", "Investors"]):
    with tabs[tab_idx]:
        bulk_data = fetch_alpha_data_v30(current_list, mode, target_date)
        # Structural Grid
        h = st.columns([1.2, 0.6, 1, 1, 1.2, 1.8, 4.5, 1.5])
        h[0].write("**Stock**"); h[1].write("**Chart**"); h[2].write("**Price**"); h[3].write("**State**")
        h[4].write("**Strength**"); h[5].write("**Smart Stake**"); h[6].write("**Professional Analyst POV**"); h[7].write("**Action**")
        st.divider()

        buy_count = 0
        for i, symbol in enumerate(current_list):
            data = analyze_v30(bulk_data[symbol] if len(current_list) > 1 else bulk_data, risk_amt, max_allocation, sl_mult, target_date)
            if data:
                if data['state'] == "BUY": buy_count += 1
                status = st.session_state.get(f"v30_{mode}_{i}", "-")
                if status == "Bought": sig, col = ("HOLD", "blue") if data['mtf'] > 45 else ("CLOSE", "red")
                else: sig = data['state']; col = "cyan" if sig == "WAIT" else "gray" if sig == "NEUTRAL" else "green" if sig == "BUY" else "red"
                if only_buys and sig not in ["BUY", "WAIT", "HOLD"]: continue
                
                c = st.columns([1.2, 0.6, 1, 1, 1.2, 1.8, 4.5, 1.5])
                c[0].markdown(f"<span class='stock-name'>{symbol.replace('.NS','')}</span>", unsafe_allow_html=True)
                c[1].link_button("📊", f"https://www.tradingview.com/chart/?symbol=NSE:{symbol.replace('.NS','')}")
                c[2].write(f"₹{data['price']:,.2f}")
                c[3].markdown(f"<span class='state-signal' style='color:{col}'>{sig}</span>", unsafe_allow_html=True)
                c[4].progress(int(data['mtf']))
                with c[5]: 
                    st.caption(f"Exit: ₹{data['sl']}")
                    st.write(f"**Qty: {data['qty']}**")
                    st.caption(f"Risk: ₹{risk_amt}")
                c[6].info(data['pov'])
                res = c[7].selectbox("Position", ["-", "Bought", "Sold"], key=f"sel30_{mode}_{i}")
                st.session_state[f"v30_{mode}_{i}"] = res
                st.divider()
