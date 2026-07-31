import sys
import traceback

try:
    from flask import Flask, render_template, jsonify, request
    import requests
    import pandas as pd
    import numpy as np
    import json
    import os
    import time
    from datetime import datetime, timedelta
    import warnings
    warnings.filterwarnings("ignore")
    
    print("✅ همه کتابخانه‌ها با موفقیت بارگذاری شدند")
    
    app = Flask(__name__, template_folder='templates')
    
    # ============================================
    # تنظیمات اولیه
    # ============================================
    DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'trades.json')
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    
    print(f"✅ پوشه داده ایجاد شد: {DATA_FILE}")
    
    # لیست رمزارزهای مهم
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
    
    print(f"✅ {len(CRYPTO_LIST)} رمزارز بارگذاری شد")
    
    @app.route('/')
    def home():
        try:
            return render_template('index.html')
        except Exception as e:
            return f"❌ خطا در بارگذاری صفحه اصلی: {str(e)}", 500
    
    @app.route('/simulator')
    def simulator():
        try:
            return render_template('simulator.html')
        except Exception as e:
            return f"❌ خطا در بارگذاری شبیه‌ساز: {str(e)}", 500
    
    @app.route('/api/analyze')
    def analyze():
        try:
            # یک پاسخ ساده برای تست
            return jsonify({
                'test': 'API working',
                'cryptos': list(CRYPTO_LIST.values())
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/history/<crypto_id>')
    def history(crypto_id):
        return jsonify([])
    
    @app.route('/api/trades', methods=['GET', 'POST', 'DELETE'])
    def trades_api():
        if request.method == 'GET':
            return jsonify([])
        elif request.method == 'POST':
            return jsonify({'status': 'success'})
        elif request.method == 'DELETE':
            return jsonify({'status': 'success'})
    
    print("✅ همه مسیرها با موفقیت ثبت شدند")
    
    if __name__ == '__main__':
        print("🚀 برنامه در حال اجرا روی پورت 10000...")
        app.run(debug=False, host='0.0.0.0', port=10000)
    
except Exception as e:
    print("❌ خطای بحرانی در برنامه:")
    print("=" * 50)
    traceback.print_exc()
    print("=" * 50)
    sys.exit(1)
