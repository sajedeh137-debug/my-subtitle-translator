import streamlit as st
import requests
import json
import re
import time

# تنظیمات ظاهر صفحه
st.set_page_config(page_title="مترجم زیرنویس اختصاصی", page_icon="🎬", layout="centered")

st.title("🎬 دستیار ترجمه و ویرایش زیرنویس")
st.write("فایل SRT خود را آپلود کنید تا با هوش مصنوعی و لحن عامیانه ترجمه شود.")

# ورودی کلید API در منوی کناری
api_key = st.sidebar.text_input("کلید Gemini API خود را وارد کنید:", type="password")

def translate_text(text, api_key):
    if not text.strip():
        return text
    
    # ساده‌سازی پرامپت برای جلوگیری از توهم زدن مدل روی خطوط کوتاه
    prompt = f"Translate the following text into colloquial Farsi (عاميانه‌ی فارسی). Observe correct punctuation and half-spaces. Return ONLY the translated text without any explanation, quotes, or introduction:\n\n{text}"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    # تلاش مجدد در صورت بروز خطاهای موقت شبکه یا سرور
    for _ in range(2):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            res_json = response.json()
            
            if response.status_code == 200:
                translated = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                # حذف تگ‌ها یا نقل‌قول‌های احتمالی اضافه
                translated = re.sub(r'<.*?>', '', translated)
                translated = translated.replace('"', '').replace("'", "")
                if translated and not translated.startswith("THOUGHTS"):
                    return translated
            time.sleep(0.5)
        except:
            pass
    return text

# آپلودر فایل
uploaded_file = st.file_uploader("انتخاب فایل زیرنویس (SRT)", type=["srt"])

if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    content = bytes_data.decode("utf-8", errors="ignore")
    
    st.success("فایل با موفقیت بارگذاری شد!")
    
    if st.button("شروع فرآیند ترجمه پیشرفته"):
        if not api_key:
            st.error("لطفاً ابتدا کلید API خود را در منوی کناری وارد کنید.")
        else:
            # تفکیک استاندارد بلاک‌های زیرنویس
            blocks = content.replace('\r\n', '\n').strip().split('\n\n')
            new_blocks = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for index, block in enumerate(blocks):
                lines = block.split('\n')
                if len(lines) >= 3:
                    num = lines[0]         # حفظ شماره خط
                    timestamp = lines[1]   # حفظ زمان‌بندی
                    text_to_translate = "\n".join(lines[2:])
                    
                    status_text.text(f"در حال ترجمه خط {index + 1} از {len(blocks)}...")
                    
                    translated_text = translate_text(text_to_translate, api_key)
                    new_blocks.append(f"{num}\n{timestamp}\n{translated_text}")
                else:
                    new_blocks.append(block)
                
                progress_bar.progress((index + 1) / len(blocks))
            
            status_text.text("ترجمه کل فایل با موفقیت کامل شد!")
            final_srt = "\n\n".join(new_blocks)
            
            st.download_button(
                label="📥 دانلود فایل زیرنویس ترجمه شده نهایی",
                data=final_srt,
                file_name="translated_subtitle.srt",
                mime="text/plain"
            )
