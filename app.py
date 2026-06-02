import streamlit as st
import requests
import json
import re
import time

# تنظیمات ظاهر صفحه
st.set_page_config(page_title="مترجم زیرنویس اختصاصی", page_icon="🎬", layout="centered")

st.title("🎬 دستیار ترجمه زیرنویس (نسخه هوشمند و سرعتی)")
st.write("فایل SRT خود را آپلود کنید تا با سرعت بالا و فرمت پایدار ترجمه شود.")

# ورودی کلید API در منوی کناری
api_key = st.sidebar.text_input("کلید Gemini API خود را وارد کنید:", type="password")

def translate_batch_json(texts_batch, api_key):
    if not texts_batch:
        return []
    
    # تبدیل لیست متون به یک دیشکنری ساختاریافته برای فهم بهتر هوش مصنوعی
    input_data = {str(i): text for i, text in enumerate(texts_batch)}
    json_payload_string = json.dumps(input_data, ensure_ascii=False)
    
    prompt = (
        f"You are a professional subtitle translator. Translate the values of the following JSON dictionary "
        f"into colloquial Farsi (عاميانه‌ی فارسی). Keep proper punctuation and half-spaces.\n"
        f"CRITICAL: Return ONLY the raw JSON object with the exact same keys and the translated values. "
        f"Do not add any explanation, thoughts, markdown formatting, or ```json tags. Just return the valid JSON string.\n\n"
        f"Data:\n{json_payload_string}"
    )
    
    url = f"[https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=](https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=){api_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    for _ in range(3):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if response.status_code == 200:
                res_json = response.json()
                raw_reply = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                
                # پاک‌سازی متن از تگ‌های مارک‌داون احتمالی در صورت لجبازی مدل
                if raw_reply.startswith("```"):
                    raw_reply = re.sub(r'^
http://googleusercontent.com/immersive_entry_chip/0

### حرکت نهایی:
۱. در گیت‌هاب دکمه‌ی **Commit changes** را بزن.
۲. سایت را رفرش کن و بریم برای یک تست فوق‌العاده سریع و واقعی. 

این فرمت جیسون قفل لجبازی جمی‌نی را کاملاً باز می‌کند. بزن بریم!
