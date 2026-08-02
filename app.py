import streamlit as st
import google.generativeai as genai
import pypdf
import json

# ページの初期設定
st.set_page_config(page_title="PDF 4択クイズ生成アプリ", layout="centered")
st.title("📄 PDF 4択クイズ生成アプリ")

# StreamlitのSecrets機能からAPIキーを取得
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("APIキーが設定されていません。StreamlitのSecretsを設定してください。")
    st.stop()

# Geminiの初期設定
genai.configure(api_key=api_key)

# サイドバーで問題数を設定
num_questions = st.sidebar.slider("作成する問題数", min_value=1, max_value=10, value=3)

# PDFファイルのアップロード
uploaded_file = st.file_uploader("PDFファイルをアップロードしてください", type="pdf")

if uploaded_file is not None:
    # PDFからテキストを抽出
    reader = pypdf.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    if len(text.strip()) == 0:
        st.warning("PDFからテキストを抽出できませんでした。文字データが含まれているか確認してください。")
    else:
        st.success(f"PDFの読み込み完了（約 {len(text)} 文字）")
        
        if st.button("クイズを作成する"):
            with st.spinner("Geminiがクイズを生成中..."):
                # Geminiへの指示プロンプト
                prompt = f"""
                以下の文章を読み、学習用の4択クイズを{num_questions}問作成してください。
                出力は必ず以下のJSONフォーマットのみを返してください。装飾文や解説文章は不要です。

                JSONフォーマット例:
                [
                  {{
                    "question": "問題文",
                    "options": ["選択肢1", "選択肢2", "選択肢3", "選択肢4"],
                    "answer": "正解の選択肢（optionsに含まれる文字列と完全一致）",
                    "explanation": "解説文"
                  }}
                ]

                文章:
                {text[:4000]}  # 文字数上限
                """
                
                try:
                    # Gemini 1.5 Flashモデルでクイズ生成
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(
                        prompt,
                        generation_config={"response_mime_type": "application/json"}
                    )
                    
                    # 生成されたJSONを解析してセッション状態に保存
                    st.session_state.quiz_data = json.loads(response.text)
                    st.session_state.user_answers = {}
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

# クイズの表示と解答処理
if "quiz_data" in st.session_state and st.session_state.quiz_data:
    st.write("---")
    st.header("📝 クイズ")
    
    quiz = st.session_state.quiz_data
    
    for i, q in enumerate(quiz):
        st.subheader(f"問 {i+1}: {q['question']}")
        
        # ラジオボタンで選択肢を表示
        user_choice = st.radio(
            f"選択肢を選んでください（問 {i+1}）",
            q['options'],
            key=f"q_{i}",
            index=None
        )
        st.session_state.user_answers[i] = user_choice
        st.write("")

    # 採点ボタン
    if st.button("回答を提出して採点"):
        st.write("---")
        st.header("📊 採点結果")
        score = 0
        
        for i, q in enumerate(quiz):
            user_ans = st.session_state.user_answers.get(i)
            correct_ans = q['answer']
            
            if user_ans == correct_ans:
                st.success(f"問 {i+1}: 正解！ ⭕")
                score += 1
            else:
                st.error(f"問 {i+1}: 不正解 ❌ （あなたの回答: {user_ans} / 正解: {correct_ans}）")
            
            st.info(f"**解説:** {q['explanation']}")
            st.write("---")
        
        st.metric("スコア", f"{score} / {len(quiz)} 点")
