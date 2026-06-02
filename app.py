import streamlit as st
import requests
import json
import re
import time

# تنظیمات ظاهر صفحه
st.set_page_config(page_title="مترجم زیرنویس اختصاصی", page_icon="🎬", layout="centered")

st.title("🎬 دستیار ترجمه و ویرایش زیرنویس (نسخه سرعت بالا)")
st.write("فایل SRT خود را آپلود کنید تا با سرعت بالا و لحن عامیانه ترجمه شود.")

# ورودی کلید API در منوی کناری
api_key = st.sidebar.text_input("کلید Gemini API خود را وارد کنید:", type="password")

def translate_batch(texts_batch, api_key):
    if not texts_batch:
        return []
    
    # چسباندن خطوط به هم با یک جداکننده منحصربه‌فرد برای اینکه هوش مصنوعی آنها را قاطی نکند
    separator = "\n---[LINE_SEP]---\n"
    combined_text = separator.join(texts_batch)
    
    prompt = (
        f"You are a professional subtitle translator. Translate each section separated by '---[LINE_SEP]---' "
        f"into colloquial Farsi (عاميانه‌ی فارسی). Maintain proper punctuation and half-spaces.\n"
        f"CRITICAL: Keep the exact same number of sections. Maintain the '---[LINE_SEP]---' separator in your response "
        f"exactly between the translated lines. Do not add any introductory or concluding text.\n\n"
        f"Text to translate:\n{combined_text}"
    )
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    for _ in range(3):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if response.status_code == 200:
                res_json = response.json()
                translated_chunk = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                
                # تفکیک مجدد خطوط ترجمه شده
                translated_lines = translated_chunk.split('---[LINE_SEP]---')
                # پاک‌سازی خطوط از تگ‌ها و کاراکترهای اضافه
                cleaned_lines = []
                for line in translated_lines:
                    line = re.sub(r'<.*?>', '', line)
                    line = line.replace('"', '').replace("'", "").strip()
                    cleaned_lines.append(line)
                
                # بررسی اینکه تعداد خطوط ترجمه شده با ارسالی برابر باشد
                if len(cleaned_lines) == len(texts_batch):
                    return cleaned_lines
            time.sleep(2)
        except:
            time.sleep(2)
            
    # در صورت خطا، همان متن اصلی انگلیسی را برمی‌گرداند تا برنامه متوقف نشود
    return texts_batch

# آپلودر فایل
uploaded_file = st.file_uploader("انتخاب فایل زیرنویس (SRT)", type=["srt"])

if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    content = bytes_data.decode("utf-8", errors="ignore")
    
    st.success("فایل با موفقیت بارگذاری شد!")
    
    if st.button("شروع ترجمه موشکی زیرنویس"):
        if not api_key:
            st.error("لطفاً ابتدا کلید API خود را در منوی کناری وارد کنید.")
        else:
            blocks = content.replace('\r\n', '\n').strip().split('\n\n')
            
            # استخراج متون، شماره خطوط و تایم‌کدها به صورت ساختاریافته
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
            
            # دسته‌بندی خطوط در دسته‌های ۳۰ تایی برای ترجمه سریع
            batch_size = 30
            translated_all_texts = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_lines = len(texts_to_translate)
            
            for i in range(0, total_lines, batch_size):
                current_batch = texts_to_translate[i:i+batch_size]
                status_text.text(f"در حال ترجمه سریع خطوط {i + 1} تا {min(i + batch_size, total_lines)}...")
                
                translated_batch_result = translate_batch(current_batch, api_key)
                translated_all_texts.extend(translated_batch_result)
                
                progress_bar.progress(min((i + batch_size) / total_lines, 1.0))
                # یک مکث بسیار کوتاه بین دسته‌ها برای امنیت بیشتر
                time.sleep(1)
            
            # بازسازی فایل SRT نهایی
            new_blocks = []
            text_index = 0
            
            for b in valid_blocks:
                if b.get("invalid"):
                    new_blocks.append(b["orig_text"])
                else:
                    # اگر به هر دلیلی خط ترجمه شده موجود نبود، متن اصلی استفاده می‌شود
                    t_text = translated_all_texts[text_index] if text_index < len(translated_all_texts) else b["orig_text"]
                    new_blocks.append(f"{b['num']}\n{b['timestamp']}\n{t_text}")
                    text_index += 1
            
            status_text.text("ترجمه موشکی با موفقیت کامل شد!")
            final_srt = "\n\n".join(new_blocks)
            
            st.download_button(
                label="📥 دانلود فایل زیرنویس ترجمه شده نهایی",
                data=final_srt,
                file_name="translated_subtitle.srt",
                mime="text/plain"
            )
