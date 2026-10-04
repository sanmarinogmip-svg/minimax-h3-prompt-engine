import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="Studio Prompt Engine (MiniMax H3)", layout="wide", page_icon="🎦")

with st.sidebar:
    st.subheader("⚙️ System Config")
    api_key_input = st.text_input("Gemini API Key", type="password", help="ご自身のGemini APIキーを入力してください（サーバーには保存されません）")
    
    st.markdown("---")
    model_choice = st.selectbox(
        "🧠 AIモデル選択",
        [
            "gemini-3.8-flash",
            "gemini-3.5-flash-lite",
        ],
        index=0
    )

st.title("🎦 Studio Prompt Engine (Ref2VA / MiniMax H3)")
st.caption(f"Cinema-grade prompt builder tailored for MiniMax Hailuo H3 workflows (Model: {model_choice})")

def voice_settings_ui(prefix, char_num, default_gender="女性", default_age="若者・青年 (Young)"):
    c_name, c_line = st.columns([1, 2])
    with c_name:
        name = st.text_input(
            f"話者{char_num}",
            value="",
            placeholder=f"例: キャラクター{char_num}",
            key=f"{prefix}_spk_{char_num}"
        )
    with c_line:
        line = st.text_input(
            f"セリフ{char_num}",
            value="",
            placeholder=f"話者{char_num}に言わせたいセリフを入力",
            key=f"{prefix}_dlg_{char_num}"
        )
    
    col_lang, col_gender, col_age = st.columns(3)
    with col_lang:
        lang = st.selectbox(f"言語 (話者{char_num})", ["日本語 (Japanese)", "英語 (English)"], key=f"{prefix}_lang_{char_num}")
    with col_gender:
        gender = st.selectbox(f"性別 (話者{char_num})", ["女性", "男性", "中性/その他"], index=0 if default_gender=="女性" else 1, key=f"{prefix}_gen_{char_num}")
    with col_age:
        age_options = ["少年・少女 (Child)", "若者・青年 (Young)", "成人 (Adult)", "老人 (Elderly)"]
        age_idx = age_options.index(default_age) if default_age in age_options else 1
        age = st.selectbox(f"年齢層 (話者{char_num})", age_options, index=age_idx, key=f"{prefix}_age_{char_num}")
    
    col_emo, col_tone = st.columns(2)
    with col_emo:
        emotion = st.selectbox(
            f"感情 (話者{char_num})",
            ["優しい・気遣い (Gentle & Caring)", "元気・明るい (Energetic & Cheerful)", "真剣・決意 (Serious & Resolute)", "怒り・威嚇 (Angry & Aggressive)", "不安・怯え (Anxious & Fearful)", "穏やか (Calm)"],
            key=f"{prefix}_emo_{char_num}"
        )
    with col_tone:
        tone = st.text_input(
            f"声のトーン/声質補足 (話者{char_num})",
            value="",
            placeholder="例: gentle, warm, clear voice",
            key=f"{prefix}_tone_{char_num}"
        )

    return {
        "name": name,
        "line": line,
        "lang": lang,
        "gender": gender,
        "age": age,
        "emotion": emotion,
        "tone": tone
    }

c_left, c_right = st.columns([1, 1], gap="large")

with c_left:
    st.subheader("👥 キャラクター・素材参照画像 (Ref2VA)")
    t_refs = st.file_uploader(
        "リファレンス画像 (複数選択可能: <Picture 1>, <Picture 2>...)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="ref_files"
    )
    imgs = [Image.open(f) for f in t_refs] if t_refs else []
    
    if imgs:
        p_cols = st.columns(min(len(imgs), 3))
        for i, img in enumerate(imgs):
            p_cols[i % 3].image(img, caption=f"<Picture {i+1}>", use_container_width=True)

    st.markdown("---")
    st.subheader("🎬 スタイル & カメラ")
    style = st.selectbox(
        "ビジュアルスタイル",
        [
            "3D CGI Stylized (Disney/Pixar style, rich volumetric lighting)",
            "Dark Fantasy 3D",
            "Anime 3D Hybrid",
            "スタイル指定なし"
        ],
        key="ref_sty"
    )
    camera = st.selectbox(
        "カメラモーション",
        [
            "Smooth Orbit",
            "Tracking Pan",
            "Slow Push-In",
            "Fixed Camera"
        ],
        key="ref_cam"
    )

with c_right:
    st.subheader("⚔️ シーン全体の展開")
    action_text = st.text_area(
        "展開・相互アクション（日本語OK）",
        height=80,
        placeholder="例: 二人が木漏れ日の下で見つめ合い、静かに言葉を交わす",
        key="ref_act"
    )
    
    st.markdown("---")
    st.subheader("🎙️ 対話設定（話者1）")
    enable_v1 = st.checkbox("話者1の発話を含める", value=True, key="ref_ev1")
    if enable_v1:
        v_char1 = voice_settings_ui("ref", 1, default_gender="男性", default_age="若者・青年 (Young)")
    else:
        v_char1 = None
    
    st.markdown("---")
    st.subheader("🎙️ 対話設定（話者2：返答）")
    enable_v2 = st.checkbox("話者2のセリフを追加", value=False, key="ref_ev2")
    if enable_v2:
        v_char2 = voice_settings_ui("ref", 2, default_gender="女性", default_age="若者・青年 (Young)")
    else:
        v_char2 = None

    st.markdown("---")
    gen_btn = st.button("🚀 Ref2VA プロンプト生成", type="primary", use_container_width=True, key="ref_btn")

if gen_btn:
    active_key = api_key_input.strip()
    if not active_key:
        st.error("Gemini API Key を入力してください。")
    else:
        with st.spinner(f"MiniMax H3向け構造化プロンプトを構築中 ({model_choice})..."):
            try:
                genai.configure(api_key=active_key)
                model = genai.GenerativeModel(model_choice)

                system_instruction = """
                You are an expert prompt architect for MiniMax Hailuo H3 (reference generation / Ref2VA).
                
                Produce a highly structured prompt following this EXACT template:
                
                subject_definitions:
                <Define each entity, referencing <Picture 1>, <Picture 2>, etc.>
                
                summary:
                [reference generation] <One-sentence summary of the shot>
                
                retention_analysis:
                <List which elements from each <Picture X> are fully_preserved or referenced>
                
                detailed_description:
                The target video uses a {style} with {camera}.
                [Shot 1] <Vivid English description of scene action, timing, character expressions, camera movement.>
                <For dialogue, format strictly like this:
                <Subject X> (S1) opens mouth and says in a [Gender, Age Category, Tone] voice: <d>[Japanese] セリフ </d> while maintaining [expression].>
                
                overall_soundscape:
                <Ambient sound effects>
                
                non_diegetic_music:
                N/A
                
                CRITICAL RULES:
                1. Dialogue must be enclosed inside `<d>[Japanese] ... </d>`. Never include character names inside or immediately before this tag.
                2. All narration, scene directions, and voice style directives must be in fluent English.
                3. Ensure the vocal description in English matches the chosen Age and Gender (e.g. elderly female -> "gentle, warm, elderly female voice").
                
                OUTPUT FORMAT:
                Part 1: Exactly ONE markdown code block (```text ... ```) containing ONLY the full structured prompt above.
                Part 2: Concise Japanese chronological timeline (何秒に何が起きるか).
                """

                voices = []
                if enable_v1 and v_char1 and v_char1["line"].strip():
                    voices.append(v_char1)
                if enable_v2 and v_char2 and v_char2["line"].strip():
                    voices.append(v_char2)

                voice_summary = ""
                for idx, v in enumerate(voices):
                    voice_summary += f"\n- Speaker {idx+1} ({v['name']}): Line='{v['line']}', Lang={v['lang']}, Gender={v['gender']}, Age={v['age']}, Emotion={v['emotion']}, Tone='{v['tone']}'"

                user_payload = f"""
                Mode: reference generation
                Style: {style}
                Camera: {camera}
                Action Plan: {action_text}
                Voice Details: {voice_summary if voice_summary else 'No dialogue specified'}
                Number of uploaded images: {len(imgs)}
                """

                contents = [system_instruction, user_payload] + imgs
                response = model.generate_content(contents)
                st.success(f"✅ 生成完了 ({model_choice})")
                st.markdown(response.text)

            except Exception as e:
                st.error(f"生成エラー: {str(e)}")