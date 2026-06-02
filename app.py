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
    
    # تبدیل لیست متون به یک دیکشنری ساختاریافته برای ارسال به هوش مصنوعی
    input_data = {str(i): text for i, text in enumerate(texts_batch)}
    json_payload_string = json.dumps(input_data, ensure_ascii=False)
    
    prompt = (
        f"You are a professional subtitle translator. Translate the values of the following JSON dictionary "
        f"into colloquial Farsi (عاميانه‌ی فارسی). Keep proper punctuation and half-spaces.\n"
        f"CRITICAL: Keep the exact same keys in the JSON and only translate the values. Do not change the keys.\n\n"
        f"Data:\n{json_payload_string}"
    )
    
    url = f"[https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=](https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=){api_key}"
    headers = {'Content-Type': 'application/json'}
    
    # فعال‌سازی قابلیت پاسخ خام JSON در گوگل کلاینت (جلوگیری ۱۰۰٪ از ایجاد تگ‌های مارک‌داون اضافه)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    for _ in range(3):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if response.status_code == 200:
                res_json = response.json()
                raw_reply = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                
                # خواندن مستقیم داده بدون نیاز به عبارات منظم پیچیده
                output_data = json.loads(raw_reply)
                
                # بازسازی لیست بر اساس ترتیب کلیدها
                translated_lines = []
                for i in range(len(texts_batch)):
                    line = output_data.get(str(i), texts_batch[i])
                    # حذف تگ‌های احتمالی HTML درون زیرنویس
                    line = re.sub(r'<.*?>', '', line)
                    line = line.replace('"', '').replace("'", "").strip()
                    translated_lines.append(line)
                    
                return translated_lines
            time.sleep(2)
        except:
            time.sleep(2)
            
    return texts_batch

# آپلودر فایل
uploaded_file = st.file_uploader("انتخاب فایل زیرنویس (SRT)", type=["srt"])

if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    content = bytes_data.decode("utf-8", errors="ignore")
    
    st.success("فایل با موفقیت بارگذاری شد!")
    
    if st.button("شروع ترجمه موشکی و هوشمند"):
        if not api_key:
            st.error("لطفاً ابتدا کلید API خود را در منوی کناری وارد کنید.")
        else:
            blocks = content.replace('\r\n', '\n').strip().split('\n\n')
            
            valid_blocks = []
            texts_to_translate = []
            
            for block in blocks:
                lines = block.split('\n')
                if len(lines) >= 3:
                    num = lines[0]
                    timestamp = lines[1]
                    text = "\n".join(lines[2:])
                    valid_blocks.append({"num": num, "timestamp": timestamp, "orig_text": text})
                    texts_to_translate.append(text)
                else:
                    valid_blocks.append({"num": "", "timestamp": "", "orig_text": block, "invalid": True})
            
            # بسته‌های ۳۰ تایی برای ترجمه سریع و بدون افت سرعت
            batch_size = 30
            translated_all_texts = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            total_lines = len(texts_to_translate)
            
            for i in range(0, total_lines, batch_size):
                current_batch = texts_to_translate[i:i+batch_size]
                status_text.text(f"در حال ترجمه هوشمند خطوط {i + 1} تا {min(i + batch_size, total_lines)}...")
                
                translated_batch_result = translate_batch_json(current_batch, api_key)
                translated_all_texts.extend(translated_batch_result)
                
                progress_bar.progress(min((i + batch_size) / total_lines, 1.0))
                time.sleep(1.5)
            
            new_blocks = []
            text_index = 0
            
            for b in valid_blocks:
                if b.get("invalid"):
                    new_blocks.append(b["orig_text"])
                else:
                    t_text = translated_all_texts[text_index] if text_index < len(translated_all_texts) else b["orig_text"]
                    new_blocks.append(f"{b['num']}\n{b['timestamp']}\n{t_text}")
                    text_index += 1
            
            status_text.text("ترجمه با موفقیت کامل شد!")
            final_srt = "\n\n".join(new_blocks)
            
            st.download_button(
                label="📥 دانلود فایل زیرنویس ترجمه شده نهایی",
                data=final_srt,
                file_name="translated_subtitle.srt",
                mime="text/plain"
            )
