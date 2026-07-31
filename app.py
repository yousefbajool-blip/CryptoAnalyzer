=from flask import Flask, render_template, jsonify, request
import requests
import pandas as pd
import numpy as np
import json
import os
import time
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

app = Flask(__name__)

# ============================================
# تنظیمات اولیه
# ============================================
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'trades.json')
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

CRYPTO_LIST = {
    'bitcoin': 'بیت‌کوین',
    'ethereum': 'اتریوم',
    'binancecoin': 'بایننس کوین',
    'ripple': 'ریپل',
    'cardano': 'کاردانو',
    'solana': 'سولانا',
    'dogecoin': 'داوج کوین',
    'polkadot': 'پولکادات',
    'avalanche-2': 'آوالانچ',
    'chainlink': 'چین لینک',
    'litecoin': 'لایت کوین',
    'bitcoin-cash': 'بیت‌کوین کش',
    'stellar': 'استلار',
    'uniswap': 'یونی سواپ',
    'monero': 'مونرو'
}

def get_crypto_prices():
    try:
        ids = ','.join(CRYPTO_LIST.keys())
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            results = {}
            for crypto_id, crypto_name in CRYPTO_LIST.items():
                if crypto_id in data:
                    item = data[crypto_id]
                    price = float(item.get('usd', 0))
                    change = float(item.get('usd_24h_change', 0))
                    results[crypto_name] = {
                        'id': crypto_id,
                        'price': price,
                        'change': change,
                        'high': price * 1.01,
                        'low': price * 0.99
                    }
            return results
        return None
    except Exception as e:
        print(f"خطا در دریافت رمزارزها: {e}")
        return None

def get_crypto_history(crypto_id, days=7):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart?vs_currency=usd&days={days}"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            prices = data.get('prices', [])
            return [{'time': p[0], 'price': p[1]} for p in prices]
        return None
    except Exception as e:
        print(f"خطا در دریافت تاریخچه {crypto_id}: {e}")
        return None

def calculate_indicators(data):
    try:
        close_prices = [d['close'] for d in data]
        high_prices = [d['high'] for d in data]
        low_prices = [d['low'] for d in data]
        volumes = [d.get('volume', 1) for d in data]
        
        if len(close_prices) < 20:
            return None
            
        sma_20 = np.mean(close_prices[-20:])
        sma_50 = np.mean(close_prices[-50:]) if len(close_prices) >= 50 else sma_20
        
        gains, losses = 0, 0
        for i in range(1, min(15, len(close_prices))):
            diff = close_prices[-i] - close_prices[-i-1]
            if diff >= 0:
                gains += diff
            else:
                losses += abs(diff)
        rsi = 100 if losses == 0 else 100 - (100 / (1 + (gains / losses)))
        
        ema_12 = np.mean(close_prices[-12:])
        ema_26 = np.mean(close_prices[-26:]) if len(close_prices) >= 26 else np.mean(close_prices[-12:])
        macd = ema_12 - ema_26
        macd_signal = np.mean([close_prices[-i] - close_prices[-i-1] for i in range(1, 10)]) if len(close_prices) >= 10 else 0
        
        sma = np.mean(close_prices[-20:])
        std = np.std(close_prices[-20:])
        bb_high = sma + (2 * std)
        bb_low = sma - (2 * std)
        
        last_high = max(high_prices[-5:]) if len(high_prices) >= 5 else high_prices[-1]
        last_low = min(low_prices[-5:]) if len(low_prices) >= 5 else low_prices[-1]
        pivot = (last_high + last_low + close_prices[-1]) / 3
        r1 = (2 * pivot) - last_low
        s1 = (2 * pivot) - last_high
        r2 = pivot + (last_high - last_low)
        s2 = pivot - (last_high - last_low)
        
        stoch_rsi = 50
        if len(close_prices) >= 14:
            rsi_values = []
            for i in range(14, 0, -1):
                if i < len(close_prices):
                    g, l = 0, 0
                    for j in range(1, 15):
                        if i - j >= 0:
                            diff = close_prices[-i] - close_prices[-i-1]
                            if diff >= 0:
                                g += diff
                            else:
                                l += abs(diff)
                    rsi_val = 100 if l == 0 else 100 - (100 / (1 + (g / l))) if l > 0 else 50
                    rsi_values.append(rsi_val)
            if len(rsi_values) >= 14:
                min_rsi = min(rsi_values)
                max_rsi = max(rsi_values)
                if max_rsi - min_rsi > 0:
                    stoch_rsi = (rsi_values[-1] - min_rsi) / (max_rsi - min_rsi) * 100
        
        obv = 0
        for i in range(1, len(close_prices)):
            if close_prices[-i] > close_prices[-i-1]:
                obv += volumes[-i]
            elif close_prices[-i] < close_prices[-i-1]:
                obv -= volumes[-i]
        
        fib_high = max(close_prices[-20:]) if len(close_prices) >= 20 else max(close_prices)
        fib_low = min(close_prices[-20:]) if len(close_prices) >= 20 else min(close_prices)
        fib_236 = fib_low + 0.236 * (fib_high - fib_low)
        fib_382 = fib_low + 0.382 * (fib_high - fib_low)
        fib_500 = fib_low + 0.5 * (fib_high - fib_low)
        fib_618 = fib_low + 0.618 * (fib_high - fib_low)
        fib_786 = fib_low + 0.786 * (fib_high - fib_low)
        
        adx = 25
        if len(close_prices) >= 14:
            dm_plus = []
            dm_minus = []
            tr = []
            for i in range(1, 15):
                if i < len(close_prices):
                    high_diff = high_prices[-i] - high_prices[-i-1]
                    low_diff = low_prices[-i-1] - low_prices[-i]
                    dm_plus.append(max(high_diff, 0))
                    dm_minus.append(max(low_diff, 0))
                    tr.append(max(high_prices[-i] - low_prices[-i], 
                                 abs(high_prices[-i] - close_prices[-i-1]),
                                 abs(low_prices[-i] - close_prices[-i-1])))
            if len(dm_plus) > 0 and len(tr) > 0:
                di_plus = sum(dm_plus[-14:]) / sum(tr[-14:]) * 100 if sum(tr[-14:]) > 0 else 0
                di_minus = sum(dm_minus[-14:]) / sum(tr[-14:]) * 100 if sum(tr[-14:]) > 0 else 0
                dx = abs(di_plus - di_minus) / (di_plus + di_minus) * 100 if (di_plus + di_minus) > 0 else 0
                adx = dx
        
        return {
            'sma_20': round(sma_20, 2),
            'sma_50': round(sma_50, 2),
            'rsi': round(rsi, 2),
            'macd': round(macd, 4),
            'macd_signal': round(macd_signal, 4),
            'bb_high': round(bb_high, 2),
            'bb_low': round(bb_low, 2),
            'pivot': round(pivot, 2),
            'r1': round(r1, 2),
            's1': round(s1, 2),
            'r2': round(r2, 2),
            's2': round(s2, 2),
            'stoch_rsi': round(stoch_rsi, 2),
            'obv': round(obv, 2),
            'fib_236': round(fib_236, 2),
            'fib_382': round(fib_382, 2),
            'fib_500': round(fib_500, 2),
            'fib_618': round(fib_618, 2),
            'fib_786': round(fib_786, 2),
            'adx': round(adx, 2)
        }
    except Exception as e:
        print(f"خطا در محاسبه اندیکاتورها: {e}")
        return None

def generate_historical_data(price, count=60):
    data = []
    for i in range(count, 0, -1):
        noise = np.random.normal(0, price * 0.01)
        data.append({
            'close': price + noise * (i / count),
            'high': price + noise * (i / count) * 1.01,
            'low': price + noise * (i / count) * 0.99,
            'volume': max(100, price * np.random.uniform(0.5, 1.5))
        })
    data.append({'close': price, 'high': price * 1.005, 'low': price * 0.995, 'volume': price * 1})
    return data

def generate_signal(price, indicators):
    if not indicators:
        return 'NEUTRAL', 'داده‌های کافی برای تحلیل وجود ندارد', 0
    
    score = 0
    reasons = []
    
    rsi = indicators.get('rsi', 50)
    if rsi < 30:
        score += 20
        reasons.append('RSI اشباع فروش')
    elif rsi > 70:
        score -= 20
        reasons.append('RSI اشباع خرید')
    
    macd = indicators.get('macd', 0)
    macd_signal = indicators.get('macd_signal', 0)
    if macd > macd_signal:
        score += 10
        reasons.append('MACD صعودی')
    elif macd < macd_signal:
        score -= 10
        reasons.append('MACD نزولی')
    
    s1 = indicators.get('s1', price * 0.95)
    r1 = indicators.get('r1', price * 1.05)
    if price <= s1:
        score += 15
        reasons.append('قیمت در منطقه حمایت')
    elif price >= r1:
        score -= 15
        reasons.append('قیمت در منطقه مقاومت')
    
    stoch_rsi = indicators.get('stoch_rsi', 50)
    if stoch_rsi < 20:
        score += 10
        reasons.append('Stoch RSI اشباع فروش')
    elif stoch_rsi > 80:
        score -= 10
        reasons.append('Stoch RSI اشباع خرید')
    
    adx = indicators.get('adx', 25)
    if adx > 40:
        if score > 0:
            score += 10
            reasons.append('روند صعودی قوی')
        else:
            score -= 10
            reasons.append('روند نزولی قوی')
    
    bb_low = indicators.get('bb_low', price * 0.95)
    bb_high = indicators.get('bb_high', price * 1.05)
    if price <= bb_low:
        score += 10
        reasons.append('برخورد به باند پایین بولینگر')
    elif price >= bb_high:
        score -= 10
        reasons.append('برخورد به باند بالای بولینگر')
    
    if score > 25:
        return 'BUY', f'خرید قوی - {", ".join(reasons[:3])}', score
    elif score > 10:
        return 'BUY', f'خرید - {", ".join(reasons[:3])}', score
    elif score < -25:
        return 'SELL', f'فروش قوی - {", ".join(reasons[:3])}', score
    elif score < -10:
        return 'SELL', f'فروش - {", ".join(reasons[:3])}', score
    else:
        return 'NEUTRAL', f'خنثی - {", ".join(reasons[:3]) if reasons else "بدون سیگنال واضح"}', score

def get_analysis(name, price, change):
    try:
        timeframes = {}
        
        for tf in ['hourly', 'daily', 'weekly']:
            if tf == 'hourly':
                hist_data = generate_historical_data(price, 24)
            elif tf == 'daily':
                hist_data = generate_historical_data(price, 60)
            else:
                hist_data = generate_historical_data(price, 30)
            
            indicators = calculate_indicators(hist_data)
            if not indicators:
                continue
            
            signal, reason, score = generate_signal(price, indicators)
            
            if signal == 'BUY':
                signal_text = '🟢 خرید'
            elif signal == 'SELL':
                signal_text = '🔴 فروش'
            else:
                signal_text = '🟡 نگهداری'
            
            timeframes[tf] = {
                'timeframe': tf,
                'price': round(price, 2),
                'signal': signal,
                'signal_text': signal_text,
                'reason': reason,
                'score': score,
                'stop_loss': round(indicators['s1'], 2),
                'take_profit': round(indicators['r1'], 2),
                'indicators': indicators
            }
        
        return {
            'name': name,
            'change': round(change, 2),
            'timeframes': timeframes
        }
        
    except Exception as e:
        print(f"❌ خطا در تحلیل {name}: {str(e)}")
        return None

def load_trades():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_trades(trades):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(trades, f, ensure_ascii=False, indent=2)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/simulator')
def simulator():
    return render_template('simulator.html')

@app.route('/api/analyze')
def analyze():
    crypto_data = get_crypto_prices()
    if not crypto_data:
        return jsonify({'error': 'دریافت داده با خطا مواجه شد'})
    
    results = {}
    for name, data in crypto_data.items():
        analysis = get_analysis(name, data['price'], data['change'])
        if analysis:
            analysis['id'] = data['id']
            results[name] = analysis
        time.sleep(0.3)
    
    return jsonify(results)

@app.route('/api/history/<crypto_id>')
def history(crypto_id):
    days = request.args.get('days', 7, type=int)
    data = get_crypto_history(crypto_id, days)
    if data:
        return jsonify(data)
    return jsonify([])

@app.route('/api/trades', methods=['GET', 'POST', 'DELETE'])
def trades_api():
    if request.method == 'GET':
        return jsonify(load_trades())
    
    elif request.method == 'POST':
        trade = request.json
        trades = load_trades()
        trade['id'] = len(trades) + 1
        trade['date'] = datetime.now().isoformat()
        trades.append(trade)
        save_trades(trades)
        return jsonify({'status': 'success', 'trade': trade})
    
    elif request.method == 'DELETE':
        save_trades([])
        return jsonify({'status': 'success', 'message': 'همه معاملات حذف شدند'})

@app.route('/api/trades/<int:trade_id>', methods=['DELETE'])
def delete_trade(trade_id):
    trades = load_trades()
    trades = [t for t in trades if t.get('id') != trade_id]
    save_trades(trades)
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    print("🚀 برنامه تحلیلگر حرفه‌ای راه‌اندازی شد...")
    print("📌 مسیرها:")
    print("   - صفحه اصلی: http://127.0.0.1:5000/")
    print("   - شبیه‌ساز معاملاتی: http://127.0.0.1:5000/simulator")
    app.run(debug=True, host='0.0.0.0', port=5000)
