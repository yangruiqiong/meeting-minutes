import streamlit as st
import datetime
import os
import io
import numpy as np
import tempfile

st.set_page_config(page_title="会议纪要助手", page_icon="🎙️", layout="centered")

st.title("🎙️ 会议纪要助手")
st.caption("录音 / 上传音频 / 上传手写记录 → 自动生成会议纪要")

# 会议信息
st.subheader("📋 会议信息")
col1, col2 = st.columns(2)
with col1:
    attendees = st.text_input("参会人员", placeholder="张三、李四、王五")
with col2:
    topic = st.text_input("会议主题", placeholder="产品上线讨论")

st.divider()

# 输入方式
tab1, tab2, tab3 = st.tabs(["🎙️ 录音", "📂 上传音频", "📄 上传手写记录"])

transcript = ""
source = ""

# --- Tab1: 录音 ---
with tab1:
    st.info("点击下方麦克风按钮开始录音，录完后点停止")
    audio_value = st.audio_input("录音")
    if audio_value:
        st.audio(audio_value)
        if st.button("🔄 转文字并生成会议纪要", key="btn_record"):
            with st.spinner("正在加载语音识别模型，首次较慢请耐心等待..."):
                import whisper, soundfile as sf
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp.write(audio_value.getvalue())
                    tmp_path = tmp.name
                try:
                    data, sr = sf.read(tmp_path, dtype='float32')
                    if data.ndim > 1:
                        data = data.mean(axis=1)
                    if sr != 16000:
                        new_len = int(len(data) / sr * 16000)
                        data = np.interp(
                            np.linspace(0, len(data), new_len),
                            np.arange(len(data)), data
                        ).astype('float32')
                    model = whisper.load_model("base")
                    result = model.transcribe(data, language='zh')
                    st.session_state['transcript'] = result['text'].strip()
                    st.session_state['source'] = "语音录音转写"
                    st.success("转写完成！")
                finally:
                    os.unlink(tmp_path)

# --- Tab2: 上传音频 ---
with tab2:
    audio_file = st.file_uploader("上传音频文件", type=["wav", "mp3", "m4a", "ogg", "flac"])
    if audio_file:
        st.audio(audio_file)
        if st.button("🔄 转文字并生成会议纪要", key="btn_audio"):
            with st.spinner("正在识别语音，请稍候..."):
                import whisper, soundfile as sf
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp.write(audio_file.getvalue())
                    tmp_path = tmp.name
                try:
                    data, sr = sf.read(tmp_path, dtype='float32')
                    if data.ndim > 1:
                        data = data.mean(axis=1)
                    if sr != 16000:
                        new_len = int(len(data) / sr * 16000)
                        data = np.interp(
                            np.linspace(0, len(data), new_len),
                            np.arange(len(data)), data
                        ).astype('float32')
                    model = whisper.load_model("base")
                    result = model.transcribe(data, language='zh')
                    st.session_state['transcript'] = result['text'].strip()
                    st.session_state['source'] = "音频文件转写"
                    st.success("转写完成！")
                finally:
                    os.unlink(tmp_path)

# --- Tab3: 上传 Word/TXT ---
with tab3:
    st.info("上传你手写整理的 Word (.docx) 或文本 (.txt) 文件，自动整理为标准会议纪要格式")
    doc_file = st.file_uploader("上传文件", type=["docx", "txt"])
    if doc_file:
        if st.button("📋 整理为会议纪要", key="btn_doc"):
            if doc_file.name.endswith(".docx"):
                from docx import Document
                doc = Document(io.BytesIO(doc_file.getvalue()))
                text = '\n'.join([p.text for p in doc.paragraphs if p.text.strip()])
            else:
                text = doc_file.getvalue().decode('utf-8')
            st.session_state['transcript'] = text
            st.session_state['source'] = "手写记录整理"
            st.success("读取完成！")

# --- 生成会议纪要 ---
if 'transcript' in st.session_state and st.session_state['transcript']:
    st.divider()
    st.subheader("📝 会议纪要")

    now = datetime.datetime.now()
    date_str = now.strftime("%Y年%m月%d日 %H:%M")
    content = st.session_state['transcript']
    src = st.session_state.get('source', '')

    sentences = [s.strip() for s in
                 content.replace('。', '。\n').replace('！', '！\n').replace('？', '？\n').split('\n')
                 if s.strip()]

    minutes = f"""会议纪要
{'='*40}
会议时间：{date_str}
参会人员：{attendees or '（未填写）'}
会议主题：{topic or '（未填写）'}
来　　源：{src}

【原始内容】
{content}

【要点整理】
"""
    for i, s in enumerate(sentences[:15], 1):
        minutes += f"{i}. {s}\n"

    minutes += f"""
【待办事项】
（请手动补充）

{'='*40}
生成时间：{date_str}
"""

    edited = st.text_area("会议纪要（可直接编辑）", value=minutes, height=400)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button("💾 下载 TXT", data=edited.encode('utf-8'),
                           file_name=f"会议纪要_{now.strftime('%Y%m%d_%H%M')}.txt",
                           mime="text/plain")
    with col2:
        from docx import Document as DocxDoc
        doc_out = DocxDoc()
        doc_out.add_heading('会议纪要', 0)
        for line in edited.split('\n'):
            doc_out.add_paragraph(line)
        buf = io.BytesIO()
        doc_out.save(buf)
        buf.seek(0)
        st.download_button("📝 下载 Word", data=buf,
                           file_name=f"会议纪要_{now.strftime('%Y%m%d_%H%M')}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
