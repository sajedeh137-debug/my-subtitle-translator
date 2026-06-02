import requests
import json
import re
import time
import streamlit as st


def translate_batch_json(texts_batch, api_key):
    if not texts_batch:
        return []

    input_data = {
        str(i): text
        for i, text in enumerate(texts_batch)
    }

    json_payload_string = json.dumps(
        input_data,
        ensure_ascii=False
    )

    prompt = f"""
You are a professional subtitle translator.

Translate the values of this JSON into natural colloquial Persian.

Rules:
- Keep all keys exactly unchanged.
- Translate only values.
- Preserve line breaks.
- Return ONLY valid JSON.
- No explanations.
- No markdown.

JSON:
{json_payload_string}
"""

    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    for attempt in range(3):

        try:

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=120
            )

            if response.status_code != 200:
                st.error(
                    f"Gemini Error {response.status_code}\n\n{response.text}"
                )
                time.sleep(2)
                continue

            result = response.json()

            candidates = result.get("candidates")

            if not candidates:
                st.error("Gemini returned no candidates.")
                return texts_batch

            raw_reply = (
                candidates[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
                .strip()
            )

            if not raw_reply:
                st.error("Empty Gemini response.")
                return texts_batch

            try:
                output_data = json.loads(raw_reply)

            except Exception:

                json_match = re.search(
                    r'\{.*\}',
                    raw_reply,
                    re.DOTALL
                )

                if not json_match:
                    st.error(
                        f"Invalid JSON returned:\n\n{raw_reply}"
                    )
                    return texts_batch

                output_data = json.loads(
                    json_match.group(0)
                )

            translated_lines = []

            for i in range(len(texts_batch)):

                translated_text = output_data.get(
                    str(i),
                    texts_batch[i]
                )

                translated_text = re.sub(
                    r'<.*?>',
                    '',
                    translated_text
                )

                translated_lines.append(
                    translated_text.strip()
                )

            return translated_lines

        except Exception as e:

            st.error(
                f"Attempt {attempt + 1} failed:\n{str(e)}"
            )

            time.sleep(2)

    return texts_batch
