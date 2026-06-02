import streamlit as st
import requests
import json

# تنظیمات ظاهر صفحه
st.set_page_config(page_title="مترجم زیرنویس اختصاصی", page_icon="🎬", layout="centered")

st.title("🎬 دستیار ترجمه و ویرایش زیرنویس")
st.write("فایل SRT خود را آپلود کنید تا با هوش مصنوعی و لحن عامیانه ترجمه شود.")

# ورودی کلید API در منوی کناری (کاملاً امن)
api_key = st.sidebar.text_input("کلید Gemini API خود را وارد کنید:", type="password")

# تنظیم پرامپت اختصاصی برای ترجمه زیرنویس
system_prompt = (
    "تو یک مترجم و ادیتور زیرنویس حرفه‌ای هستی. وظیفه داری متن‌هایی که بهت داده میشه رو "
    "به زبان عامیانه‌ی فارسی ترجمه کنی. رعایت نکات نگارشی و استفاده درست از نیم‌فاصله‌ها "
    "برای من حیاتیه. فقط و فقط متن ترجمه شده رو برگردون و هیچ توضیحی اضافه نکن."
)

def translate_text(text, api_key):
    if not api_key:
        return text
    
    # استفاده از مدل جدید و پایدار سیستم گوگل جهت جلوگیری از ارور 404
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
            return res_json['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            return f"[خطا از سمت گوگل: {res_json.get('error', {}).get('message', 'خطای ناشناخته')}]"
    except Exception as e:
        return f"[خطا در شبکه: {str(e)}]"

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
            blocks = content.strip().split('\n\n')
            new_blocks = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for index, block in enumerate(blocks):
                lines = block.split('\n')
                if len(lines) >= 3:
                    num = lines[0]
                    timestamp = lines[1]
                    text_to_translate = "\n".join(lines[2:])
                    
                    status_text.text(f"در حال ترجمه خط {index + 1} از {len(blocks)}...")
                    translated_text = translate_text(text_to_translate, api_key)
                    
                    new_blocks.append(f"{num}\n{timestamp}\n{translated_text}")
                else:
                    new_blocks.append(block)
                
                progress_bar.progress((index + 1) / len(blocks))
            
            status_text.text("ترجمه با موفقیت کامل شد!")
            final_srt = "\n\n".join(new_blocks)
            
            st.download_button(
                label="📥 دانلود فایل زیرنویس ترجمه شده",
                data=final_srt,
                file_name="translated_subtitle.srt",
                mime="text/plain"
            )
