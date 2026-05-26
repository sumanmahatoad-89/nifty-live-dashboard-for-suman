import streamlit as st
import pandas as pd
import requests
import time

# --- 1. LOGIN SECURITY ---
def check_password():
    """Returns True if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == st.secrets["PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

# --- 2. DATA FETCHING ---
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-US,en;q=0.9'
}

def get_nse_data():
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers) # Set cookies
    url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    response = session.get(url, headers=headers).json()
    return response

# --- 3. DASHBOARD UI ---
if check_password():
    st.set_page_config(page_title="My Nifty Live", layout="wide")
    st.title("📈 Nifty 50 Live Option Chain")

    try:
        data = get_nse_data()
        underlying_price = data['records']['underlyingValue']
        timestamp = data['records']['timestamp']
        
        # Metrics Row
        col1, col2, col3 = st.columns(3)
        col1.metric("Nifty Spot", underlying_price)
        col2.metric("Last Updated", timestamp)
        
        # Option Chain Processing
        records = data['filtered']['data']
        oc_list = []
        for r in records:
            oc_list.append({
                'Strike': r['strikePrice'],
                'CE OI': r['CE']['openInterest'] if 'CE' in r else 0,
                'CE CHG OI': r['CE']['changeinOpenInterest'] if 'CE' in r else 0,
                'CE LTP': r['CE']['lastPrice'] if 'CE' in r else 0,
                'PE LTP': r['PE']['lastPrice'] if 'PE' in r else 0,
                'PE CHG OI': r['PE']['changeinOpenInterest'] if 'PE' in r else 0,
                'PE OI': r['PE']['openInterest'] if 'PE' in r else 0,
            })
        
        df = pd.DataFrame(oc_list)
        
        # Filter for ATM strikes (optional)
        atm_strike = round(underlying_price / 50) * 50
        df = df[(df['Strike'] >= atm_strike - 500) & (df['Strike'] <= atm_strike + 500)]

        # Highlight ATM
        st.table(df.style.highlight_max(axis=0, subset=['CE OI', 'PE OI'], color='#f8d7da'))
        
        if st.button("Refresh Data"):
            st.rerun()
            
    except Exception as e:
        st.error(f"Waiting for NSE Data... (Market might be closed or API limited)")
        time.sleep(5)
