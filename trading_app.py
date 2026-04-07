import warnings
import sys
import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import gspread # Google Sheets Bridge
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, date, timedelta

# --- SYSTEM ANCHOR ---
sys.modules['warnings'] = warnings 

# --- 0. GOOGLE DRIVE PERSISTENCE ENGINE ---
def connect_to_drive():
    try:
        # Note: You must add your credentials to st.secrets or a local file
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        client = gspread.authorize(creds)
        return client.open("Project_Alpha_Archive")
    except Exception as e:
        return None

def save_daily_swing_data(date_str, df_results):
    sheet = connect_to_drive()
    if sheet:
        try:
            # Check if worksheet for the date exists, else create it
            try:
                worksheet = sheet.add_worksheet(title=date_str, rows="100", cols="20")
            except:
                worksheet = sheet.worksheet(date_str)
            
            # Clear and update with new data
            worksheet.clear()
            worksheet.update([df_results.columns.values.tolist()] + df_results.values.tolist())
        except:
            pass

def load_historical_swing_data(date_str):
    sheet = connect_to_drive()
    if sheet:
        try:
            worksheet = sheet.worksheet(date_str)
            return pd.DataFrame(worksheet.get_all_records())
        except:
            return None
    return None

# --- 1. SETTINGS & CSS (FROZEN FROM v28.1) ---
st.set_page_config(layout="wide", page_title="Project Alpha v32.0", page_icon="🛡️")

st.markdown("""
    <style>
    [data-testid="stVerticalBlock"] > div { padding-top: 0.05rem; padding-bottom: 0.05rem; }
    hr { margin-top: 0.3rem !important; margin-bottom: 0.3rem !important; }
    [data-testid="stMetric"] { background-color: #262730 !important; padding: 15px !important; border-radius: 12px !important; border: 1px solid #41444C !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.8rem !important; font-weight: 700 !important; }
    
    @media (max-width: 768px) {
        [data-testid="stHorizontalBlock"] { display: flex !important; flex-direction: row !important; overflow-x: auto !important; white-space: nowrap !important; gap: 15px !important; }
        [data-testid="column"] { min-width: 140px !important; flex: 0 0 auto !important; }
        [data-testid="column"]:nth-child(7) { min-width: 400px !important; }
    }
    .stock-name, .state-signal { font-size: 14px; font-weight: bold; }
    .stInfo { padding: 12px !important; font-size: 13px !important; line-height: 1.5 !important; border-left: 5px solid #2e9aff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR COMMAND CENTER ---
st.sidebar.title("🛡️ Alpha Command")
total_capital, risk_amt, max_allocation = 200000, 2000, 20000

st.sidebar.subheader("📅 Archive Timeline")
# Updated: Date Dropdown for toggling history
target_date = st.sidebar.date_input("Analysis Date", value=date.today(), max_value=date.today())
date_str = target_date.strftime('%Y-%m-%d')

st.sidebar.subheader("⚙️ Portfolio Filters")
cap_choice = st.sidebar.selectbox("Market Segment", ["Large Cap", "Mid Cap", "Small Cap"])
search_q = st.sidebar.text_input("🔍 Search Terminal", "").upper()
sl_mult = st.sidebar.slider("Volatility Buffer (SL Multiplier)", 1.0, 3.0, 1.5)
only_buys = st.sidebar.toggle("🔥 Actionable Alpha Only", value=False)

# --- 3. REPOSITORY (FROZEN) ---
TICKER_MAP = {
    "Large Cap": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BHARTIARTL.NS", "SBIN.NS", "INFY.NS", "LICI.NS", "ITC.NS", "HUL.NS", "LT.NS", "BAJFINANCE.NS", "AXISBANK.NS", "KOTAKBANK.NS", "SUNPHARMA.NS", "ADANIENT.NS", "TATAMOTORS.NS", "MARUTI.NS", "NTPC.NS", "TITAN.NS", "ONGC.NS", "ADANIPORTS.NS", "POWERGRID.NS", "ASIANPAINT.NS", "HCLTECH.NS", "COALINDIA.NS", "TATASTEEL.NS", "BAJAJFINSV.NS", "ULTRACEMCO.NS", "M&M.NS", "JSWSTEEL.NS", "GRASIM.NS", "NESTLEIND.NS", "WIPRO.NS", "LTIM.NS", "HINDALCO.NS", "SBILIFE.NS", "BAJAJ-AUTO.NS", "ADANIGREEN.NS", "BEL.NS", "TATAELXSI.NS", "TRENT.NS", "VBL.NS", "SHRIRAMFIN.NS", "TATACONSUM.NS", "CIPLA.NS", "DRREDDY.NS", "BPCL.NS", "EICHERMOT.NS", "BRITANNIA.NS", "GAIL.NS", "INDIGO.NS", "HAL.NS", "ADANIPOWER.NS", "DLF.NS", "IOC.NS", "JINDALSTEL.NS", "CHOLAFIN.NS", "SIEMENS.NS", "TATACOMM.NS", "ABB.NS", "AMBUJACEM.NS", "BANKBARODA.NS", "BERGEPAINT.NS", "CANBK.NS", "COLPAL.NS", "DABUR.NS", "DIVISLAB.NS", "EXIDEIND.NS", "FEDERALBNK.NS", "GLAND.NS", "GODREJCP.NS", "HAVELLS.NS", "HEROMOTOCO.NS", "HINDZINC.NS", "ICICIPRULI.NS", "IDFCFIRSTB.NS", "INDUSINDBK.NS", "IRCTC.NS", "JSWENERGY.NS", "JUBLFOOD.NS", "LUPIN.NS", "MARICO.NS", "MCDOWELL-N.NS", "MUTHOOTFIN.NS", "NMDC.NS", "OBEROIRLTY.NS", "PIDILITIND.NS", "PNB.NS", "RECLTD.NS", "MOTHERSON.NS", "SHREECEM.NS", "SRF.NS", "TATACHEM.NS", "TATAPOWER.NS", "TVSMOTOR.NS", "UPL.NS", "VEDL.NS", "YESBANK.NS", "ZOMATO.NS", "JIOFIN.NS"],
    "Mid Cap": ["BSE.NS", "INDUSTOWER.NS", "POLYCAB.NS", "GMRINFRA.NS", "ASHOKLEY.NS", "BHEL.NS", "MAXHEALTH.NS", "PERSISTENT.NS", "MANKIND.NS", "BHARATFORG.NS", "OIL.NS", "AUROPHARMA.NS", "SWIGGY.NS", "NHPC.NS", "NYKAA.NS", "HPCL.NS", "POLICYBZR.NS", "AUBANK.NS", "NAUKRI.NS", "PAYTM.NS", "ALKEM.NS", "MCX.NS", "SBICARD.NS", "DIXON.NS", "FORTIS.NS", "LAURUSLABS.NS", "PHOENIXLTD.NS", "APLAPOLLO.NS", "MAXFSL.NS", "TIINDIA.NS", "PRESTIGE.NS", "SUPREMEIND.NS", "GODREJPROP.NS", "MPHASIS.NS", "COFORGE.NS", "VOLTAS.NS", "CONCOR.NS", "CUMMINSIND.NS", "ESCORTS.NS", "GUJGASLTD.NS", "IDBI.NS", "IGL.NS", "INDIANB.NS", "IPCALAB.NS", "JKCEMENT.NS", "LICHSGFIN.NS", "LTTS.NS", "MRF.NS", "OFSS.NS", "PAGEIND.NS", "PETRONET.NS", "PFC.NS", "RAMCOCEM.NS", "RVNL.NS", "SYNGENE.NS", "UNIONBANK.NS", "WHIRLPOOL.NS", "ZEEL.NS", "ABFRL.NS", "ACC.NS", "AJANTPHARM.NS", "APOLLOTYRE.NS", "BALKRISIND.NS", "BANDHANBNK.NS", "BATAINDIA.NS", "BEL.NS", "BIOCON.NS", "COROMANDEL.NS", "CROMPTON.NS", "DEEPAKNTR.NS", "DELHIVERY.NS", "GLENMARK.NS", "IEX.NS", "INDHOTEL.NS", "L&TFH.NS", "ASTRAL.NS", "KEI.NS", "KPITTECH.NS", "MAZDOCK.NS", "SJVN.NS", "SUNTV.NS", "UNOMINDA.NS", "MANYAVAR.NS", "PATANJALI.NS", "MRPL.NS", "ARCHEAN.NS", "KAYNES.NS", "GODREJIND.NS", "CENTURYPLY.NS", "METROPOLIS.NS", "TATACOMM.NS", "UPL.NS"],
    "Small Cap": ["IREDA.NS", "HINDCOPPER.NS", "ASTERDM.NS", "NH.NS", "POONAWALLA.NS", "SONACOMS.NS", "NAVINFLUOR.NS", "ANANDRATHI.NS", "KARURVYSYA.NS", "HIMATSEIDE.NS", "NBCC.NS", "WELCORP.NS", "LALPATHLAB.NS", "AMBER.NS", "TATATECH.NS", "ANGELONE.NS", "MANAPPURAM.NS", "AEGISLOG.NS", "WOCKPHARMA.NS", "PNBHOUSING.NS", "CESC.NS", "AFFLE.NS", "PPLPHARMA.NS", "RBLBANK.NS", "IIFL.NS", "NATCOPHARM.NS", "CITYUNIONB.NS", "CAMS.NS", "FIVESTAR.NS", "INOXWIND.NS", "KEC.NS", "KFINTECH.NS", "PGELECTRO.NS", "REDINGTON.NS", "RPOWER.NS", "SUVENPHAR.NS", "ZENSARTECH.NS", "IRFC.NS", "HUDCO.NS", "PCJEWELLER.NS", "COCHINSHIP.NS", "GRSE.NS", "GOKEX.NS", "SWANENERGY.NS", "TEJASNET.NS", "HFCL.NS", "ITI.NS", "RAILTEL.NS", "GPIL.NS", "TIRUMALCHM.NS", "KOPRAN.NS", "MOREPENLAB.NS", "MARKSANS.NS", "SMSPHARMA.NS", "AARTIDRUGS.NS", "GRANULES.NS", "ERIS.NS", "PFIZER.NS", "JBCHEPHARM.NS", "SANWS.NS", "HINDWARE.NS", "CERA.NS", "KAJARIACER.NS", "SOMANYCERA.NS", "SUNTECK.NS", "PURVA.NS", "MAHLIFE.NS", "BRIGADE.NS", "SOBHA.NS", "EASEMYTRIP.NS", "BLS.NS", "THOMASCOOK.NS", "VIPIND.NS", "SYMPHONY.NS", "EUREKAFORBE.NS", "ORIENTBELL.NS", "BORORENEW.NS", "GENUSPOWER.NS", "HPL.NS", "BOROSIL.NS", "LAOPALA.NS", "KIRLFERROS.NS", "THANGAMAYL.NS", "INOXINDIA.NS", "JWL.NS", "TITAGARH.NS", "SIGNATURE.NS", "HAPPYFORG.NS", "KIRLOSENG.NS", "RAMRAT.NS"]
}

# --- 4. ENGINE (FROZEN NARRATIVE) ---
def generate_elaborated_note(state, gc, rsi):
    gc_status = "🌟 Golden Cross Confirmed: Long-term floor active." if gc else "🌑 No Structural Floor."
    notes = {
        "BUY": f"**BULLISH IGNITION:** Trading firmly above 20-EMA with RSI ({rsi:.1f}) in Power Zone. {gc_status}",
        "WAIT": f"**RECOVERY ALERT:** RSI ({rsi:.1f}) curling up from oversold. Monitoring close above EMA20. {gc_status}",
        "NEUTRAL": f"**EQUILIBRIUM:** Price hugging 20-EMA mean. RSI ({rsi:.1f}) indicates sideways chop. {gc_status}",
        "SELL": f"**BEARISH DOMINANCE:** Asset structurally compromised. Below major trendlines. {gc_status}"
    }
    return notes.get(state, "Scanning...")

@st.cache_data(ttl=600)
def fetch_alpha_data_v28(tickers, target_date):
    # Always fetch extra padding to ensure EMA200 works even for historical dates
    return yf.download(tickers, period="2y", interval="1d", group_by='ticker', auto_adjust=True, progress=False)

def analyze_swing(df, risk_val, alloc_val, mult, target_date):
    try:
        # Slice data to the selected historical date
        df = df[df.index <= pd.Timestamp(target_date)]
        if df.empty or len(df) < 200: return None
        
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['EMA200'] = ta.ema(df['Close'], length=200)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        lp, rsi = float(df['Close'].iloc[-1]), df['RSI'].iloc[-1]
        atr, ema20, ema200 = df['ATR'].iloc[-1], df['EMA20'].iloc[-1], df['EMA200'].iloc[-1]
        
        sl = round(lp - (mult * atr), 2)
        qty = min(int(risk_val / (lp - sl)), int(alloc_val / lp)) if lp > sl else 0
        gc = ema20 > ema200
        state = "BUY" if rsi > 55 else "WAIT" if rsi > df['RSI'].iloc[-2] else "NEUTRAL" if 45 <= rsi <= 55 else "SELL"
        
        mtf = 60 + (20 if lp > ema20 else 0) + (20 if rsi > 55 else 0)
        pov = generate_elaborated_note(state, gc, rsi)
        
        return {"symbol": "", "price": lp, "mtf": mtf, "state": state, "sl": sl, "qty": qty, "pov": pov}
    except: return None

# --- 5. RENDERER (SWING TRADING ONLY ARCHIVE) ---
m_indices = {"Nifty 50": "^NSEI", "Bank Nifty": "^NSEBANK", "Nifty IT": "^CNXIT"}
m_cols = st.columns(4) 
for i, (name, ticker) in enumerate(m_indices.items()):
    try:
        d = yf.Ticker(ticker).history(period="5d")
        m_cols[i].metric(name, f"{d['Close'].iloc[-1]:,.0f}", f"{((d['Close'].iloc[-1]-d['Close'].iloc[-2])/d['Close'].iloc[-2])*100:.2f}%")
    except: pass
m_cols[3].metric("Archive Status", "CONNECTED", date_str)

st.divider()

current_list = [t for t in TICKER_MAP[cap_choice] if search_q in t]
tabs = st.tabs(["Active Terminal", "📜 Archive View"])

with tabs[0]: # ACTIVE TAB
    with st.spinner(f"Simulating Swing State for {date_str}..."):
        bulk_data = fetch_alpha_data_v28(current_list, target_date)
    
    h = st.columns([1.2, 0.6, 1, 1, 1.2, 1.8, 4.5, 1.5])
    h[0].write("**Stock**"); h[1].write("**Chart**"); h[2].write("**Price**"); h[3].write("**State**")
    h[4].write("**Strength**"); h[5].write("**Smart Stake**"); h[6].write("**Analyst POV**"); h[7].write("**Action**")
    st.divider()

    daily_results = []
    for i, symbol in enumerate(current_list):
        data = analyze_swing(bulk_data[symbol] if len(current_list)>1 else bulk_data, risk_amt, max_allocation, sl_mult, target_date)
        if data:
            data["symbol"] = symbol
            daily_results.append(data)
            
            # Filter logic
            if only_buys and data['state'] not in ["BUY", "WAIT"]: continue

            c = st.columns([1.2, 0.6, 1, 1, 1.2, 1.8, 4.5, 1.5])
            c[0].markdown(f"<span class='stock-name'>{symbol.replace('.NS','')}</span>", unsafe_allow_html=True)
            c[1].link_button("📊", f"https://www.tradingview.com/chart/?symbol=NSE:{symbol.replace('.NS','')}")
            c[2].write(f"₹{data['price']:,.2f}")
            c[3].write(data['state'])
            c[4].progress(int(data['mtf']))
            with c[5]: st.write(f"**Qty: {data['qty']}**"); st.caption(f"Risk: ₹{risk_amt}")
            c[6].info(data['pov'])
            res = c[7].selectbox("Position", ["-", "Bought", "Sold"], key=f"s_{date_str}_{symbol}")
    
    # Auto-save button for daily persistence
    if st.button("🚀 Push to Drive Archive"):
        res_df = pd.DataFrame(daily_results)
        save_daily_swing_data(date_str, res_df)
        st.success(f"Archived {len(res_df)} stocks for {date_str} to your Drive.")

with tabs[1]: # ARCHIVE VIEW TAB
    st.subheader(f"Historical Lookup: {date_str}")
    hist_df = load_historical_swing_data(date_str)
    if hist_df is not None:
        st.dataframe(hist_df, use_container_width=True)
    else:
        st.warning("No archived data found for this date. Run the 'Push to Drive' on the Active tab first.")
