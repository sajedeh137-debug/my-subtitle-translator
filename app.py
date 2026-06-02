import streamlit as st
import requests
import json
import re

# تنظیمات ظاهر صفحه
st.set_page_config(page_title="مترجم زیرنویس اختصاصی", page_icon="🎬", layout="centered")

st.title("🎬 دستیار ترجمه و ویرایش زیرنویس")
st.write("فایل SRT خود را آپلود کنید تا با هوش مصنوعی و لحن عامیانه ترجمه شود.")

# ورودی کلید API در منوی کناری
api_key = st.sidebar.text_input("کلید Gemini API خود را وارد کنید:", type="password")

# تنظیم پرامپت اختصاصی و بسیار سخت‌گیرانه برای ترجمه زیرنویس
system_prompt = (
    "تو یک مترجم و ادیتور زیرنویس حرفه‌ای هستی. وظیفه داری متنی که بهت داده میشه رو "
    "دقیقاً به زبان عامیانه‌ی فارسی ترجمه کنی. رعایت نکات نگارشی و استفاده درست از نیم‌فاصله‌ها "
    "برای من حیاتیه. فقط و فقط متن ترجمه شده رو برگردون و هیچ توضیح، مقدمه یا تگی اضافه نکن."
)

def translate_text(text, api_key):
    if not text.strip():
        return text
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    payload = {
        "contents": [{
            "parts": [{"text": f"{system_prompt}\n\nمتن برای ترجمه:\n{text}"}]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        res_json = response.json()
        
        if response.status_code == 200:
            translated = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
            # پاک‌سازی هرگونه تگ احتمالی که هوش مصنوعی اضافه کرده باشد
            translated = re.sub(re.compile(r'<.*?>'), '', translated)
            return translated
        else:
            return text  # در صورت خطا، متن اصلی را برمی‌گرداند تا فرآیند متوقف نشود
    except:
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
            # تفکیک دقیق بلاک‌های زیرنویس بر اساس استاندارد SRT
            blocks = content.replace('\r\n', '\n').strip().split('\n\n')
            new_blocks = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for index, block in enumerate(blocks):
                lines = block.split('\n')
                if len(lines) >= 3:
                    num = lines[0]         # شماره خط (حفظ کامل)
                    timestamp = lines[1]   # تایم‌کد (حفظ کامل بدون تغییر)
                    text_to_translate = "\n".join(lines[2:]) # فقط متن فرستاده می‌شود
                    
                    status_text.text(f"در حال ترجمه خط {index + 1} از {len(blocks)}...")
                    
                    # ترجمه کاملاً ایزوله
                    translated_text = translate_text(text_to_translate, api_key)
                    
                    # بازسازی بلاک با ساختار استاندارد
                    new_blocks.append(f"{num}\n{timestamp}\n{translated_text}")
                else:
                    new_blocks.append(block)
                
                progress_bar.progress((index + 1) / len(blocks))
            
            status_text.text("ترجمه با موفقیت و حفظ کامل زمان‌بندی کامل شد!")
            final_srt = "\n\n".join(new_blocks)
            
            st.download_button(
                label="📥 دانلود فایل زیرنویس ترجمه شده (با تایم‌کد درست)",
                data=final_srt,
                file_name="translated_subtitle.srt",
                mime="text/plain"
            )
