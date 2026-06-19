import streamlit as st
import json
import numpy as np
import pickle
import random
import google.generativeai as genai

# Konfigurasi Gemini API (Ganti dengan API Key milikmu)
API_KEY = "AQ.Ab8RN6LKuD2c7o0xAUpJh5Kw_K0SraqdwFNSJCoPyHKMHYzijw"
genai.configure(api_key=API_KEY)
llm_model = genai.GenerativeModel('gemini-1.5-flash')

# 1. Konfigurasi Halaman 
st.set_page_config(page_title="Asisten Basis Data", page_icon="✨", layout="wide")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# 2. Fungsi Load Komponen Lokal (Fase Retrieval)
@st.cache_resource
def load_chatbot_components():
    with open('intents.json') as file:
        data = json.load(file)
    with open('chatbot_db_model.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('vectorizer.pkl', 'rb') as f:
        vectorizer = pickle.load(f)
    return data, model, vectorizer

try:
    data, model, vectorizer = load_chatbot_components()
except Exception as e:
    st.error(f"Gagal memuat komponen. Error: {e}")
    st.stop()

# 3. Sidebar (Menu Kiri ala Gemini)
with st.sidebar:
    st.title("✨ Asisten AI")
    st.caption("Mata Kuliah Basis Data")
    
    # Tombol untuk mereset riwayat obrolan
    if st.button("➕ Chat Baru", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "Halo! Saya asisten virtual AI untuk mata kuliah Basis Data. Apa yang ingin kita pelajari hari ini?"}
        ]
        st.rerun()
        
    st.divider()
    st.info("💡 **Tips:** Coba tanyakan tentang ERD, Normalisasi, DDL, atau DML.")

# 4. Manajemen Riwayat Percakapan
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Halo! Saya asisten virtual AI untuk materi Basis Data. Apa yang ingin kita pelajari hari ini?"}
    ]

st.title("✨ Chat dengan Asisten Basis Data")

for message in st.session_state.messages:
    avatar = "🧑‍💻" if message["role"] == "user" else "✨"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# 5. Input Chat & Pemrosesan
if user_input := st.chat_input("Tanyakan sesuatu tentang Basis Data..."):
    
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("Menganalisis materi..."):
        # FASE 1: RETRIEVAL (Menggunakan model ML lokal)
        input_vector = vectorizer.transform([user_input.lower()]).toarray()
        predicted_tag = model.predict(input_vector)[0]
        probabilities = model.predict_proba(input_vector)
        confidence = np.max(probabilities)

        if confidence > 0.50:
            # Mengambil jawaban dasar dari intents.json
            base_knowledge = ""
            for intent in data['intents']:
                if intent['tag'] == predicted_tag:
                    base_knowledge = random.choice(intent['responses'])
                    break
            
            # FASE 2: AUGMENTATION (Menggabungkan konteks)
            prompt = f"""
            Kamu adalah asisten dosen praktikum Basis Data yang ramah dan suportif.
            Seorang mahasiswa bertanya: "{user_input}"
            
            Gunakan HANYA fakta materi berikut ini untuk menjawab: "{base_knowledge}"
            
            Tugasmu:
            Susun ulang fakta materi di atas menjadi jawaban yang natural, interaktif, dan mudah dipahami mahasiswa. 
            Jangan menambahkan materi dari luar fakta yang diberikan. Jelaskan dengan gaya bahasa yang bervariasi.
            """
            
            # FASE 3: GENERATION (Mengirim ke Gemini)
            try:
                response = llm_model.generate_content(prompt)
                bot_response = response.text
            except Exception as e:
                bot_response = f"*(Sistem AI sedang sibuk, menggunakan jawaban standar)*\n\n{base_knowledge}"
        else:
            bot_response = "Maaf, pertanyaan tersebut sepertinya di luar cakupan materi Basis Data kita saat ini. Bisa tolong gunakan istilah yang lebih spesifik mengenai ERD, Normalisasi, atau SQL?"

    with st.chat_message("assistant", avatar="✨"):
        st.markdown(bot_response)
    st.session_state.messages.append({"role": "assistant", "content": bot_response})