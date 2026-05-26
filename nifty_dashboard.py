import streamlit as st
import pandas as pd
import requests
import time

# --- 1. LOGIN SECURITY ---
def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("Enter Dashboard Password", type="password", on_change=lambda: st.session_state.update({"password_correct": st.session_state["pw_input"] == st.secrets["PASSWORD"]}), key="pw_input")
        return False
    return st.session_state["password_correct"]

# --- 2. IMPROVED DATA FETCHING (Stealth Mode) ---
def get_nse_data():
    base_url = "https://www.nseindia.com/"
    # The API URL for Nifty Option Chain
    api_url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": base_url
    }

    session = requests.Session()
    # Step A: Visit the home page first to get cookies
    session.get(base_url, headers=headers, timeout=10)
    
    # Step B: Now fetch the actual data
    response = session.get(api_url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        return response.json()
    else:
        # This helps us see if we are being blocked (403)
        st.error(f"NSE Error Code: {response.status_code}. The site is blocking the server.")
        return None

# --- 3. DASHBOARD UI ---
if check_password():
    st.set_page_config(page_title="My Nifty Live", layout="wide")
    st.title("📈 Nifty 50 Live Option Chain")

    try:
        data = get_nse_data()
        if data:
            underlying_price = data['records']['underlyingValue']
            timestamp = data['records']['timestamp']
            
            # Show stats
            c1, c2, c3 = st.columns(3)
            c1.metric("Nifty Spot", f"₹{underlying_price}")
            c2.metric("Last Updated", timestamp)
            
            # Process Data
            records = data['filtered']['data']
            oc_data = []
            for r in records:
                row = {'Strike': r['strikePrice']}
                if 'CE' in r:
                    row.update({'CE_OI': r['CE']['openInterest'], 'CE_CHG': r['CE']['changeinOpenInterest'], 'CE_LTP': r['CE']['lastPrice']})
                if 'PE' in r:
                    row.update({'PE_LTP': r['PE']['lastPrice'], 'PE_CHG': r['PE']['changeinOpenInterest'], 'PE_OI': r['PE']['openInterest']})
                oc_data.append(row)
            
            df = pd.DataFrame(oc_data)
            
            # Filter to show strikes near current price
            atm_strike = round(underlying_price / 50) * 50
            df = df[(df['Strike'] >= atm_strike - 300) & (df['Strike'] <= atm_strike + 300)]
            
            # Stylized Table
            st.dataframe(df.style.background_gradient(subset=['CE_OI', 'PE_OI'], cmap='YlGn'), use_container_width=True)
            
            if st.button("Manual Refresh"):
                st.rerun()
        else:
            st.warning("Could not fetch data. Check if market is open (9:15 AM - 3:30 PM IST).")
            
    except Exception as e:
        st.error(f"Error occurred: {str(e)}")
