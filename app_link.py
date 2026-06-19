import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# --- KONFIGURASI GEMINI ---
API_KEY = "AQ.Ab8RN6LKuD2c7o0xAUpJh5Kw_K0SraqdwFNSJCoPyHKMHYzijw"
try:
    genai.configure(api_key=API_KEY)
    llm_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("Konfigurasi API Key Gagal. Periksa kembali Key Anda.")

st.set_page_config(page_title="Web RAG AI", page_icon="🌐", layout="wide")

# Menyembunyikan menu bawaan
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("🌐 Chatbot AI dengan Database Link Web")
st.write("Masukkan link artikel atau materi kuliah. AI akan membaca halamannya dan menjawab berdasarkan teks di dalamnya.")

# --- AREA INPUT LINK (RETRIEVAL DARI WEB) ---
if "web_context" not in st.session_state:
    st.session_state.web_context = ""

with st.sidebar:
    st.title("📚 Sumber Pengetahuan")
    url_input = st.text_input("Masukkan URL/Link Artikel:")
    
    if st.button("📥 Pelajari Link Ini", use_container_width=True):
        if url_input:
            with st.spinner("Sedang membaca website..."):
                try:
                    # Mengunduh isi website
                    response = requests.get(url_input, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Mengambil semua teks dari paragraf (<p>)
                    paragraphs = soup.find_all('p')
                    scraped_text = " ".join([p.get_text() for p in paragraphs])
                    
                    # Membatasi jumlah teks (misal 5000 karakter) agar tidak berat
                    st.session_state.web_context = scraped_text[:5000] 
                    st.success("Berhasil! AI sudah membaca isi link tersebut.")
                except Exception as e:
                    st.error(f"Gagal membaca link. Pastikan link aktif. Error: {e}")
        else:
            st.warning("Masukkan link terlebih dahulu!")
            
    st.divider()
    if st.button("🗑️ Hapus Obrolan"):
        st.session_state.messages = []
        st.rerun()

# --- AREA CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Halo! Silakan masukkan link di menu sebelah kiri, lalu tanyakan isinya kepada saya."}]

for message in st.session_state.messages:
    avatar = "🧑‍💻" if message["role"] == "user" else "✨"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

if user_input := st.chat_input("Tanyakan sesuatu tentang isi link tersebut..."):
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("Mencari jawaban dari teks web..."):
        # Mengecek apakah user sudah memasukkan link atau belum
        if st.session_state.web_context == "":
            bot_response = "Tolong masukkan dan 'Pelajari' link di menu sebelah kiri terlebih dahulu ya, agar saya punya bahan bacaan."
        else:
            # FASE AUGMENTATION & GENERATION
            prompt = f"""
            Tugasmu adalah menjawab pertanyaan pengguna HANYA berdasarkan teks referensi web di bawah ini.
            Jika jawabannya tidak ada di dalam teks referensi, katakan "Maaf, informasi tersebut tidak ada di dalam link yang diberikan."
            
            Teks Referensi Web:
            "{st.session_state.web_context}"
            
            Pertanyaan Pengguna: "{user_input}"
            """
            
            try:
                ai_response = llm_model.generate_content(prompt)
                bot_response = ai_response.text
            except Exception as e:
                bot_response = f"*(Gagal menghubungi Gemini. Error: {e})*"

    with st.chat_message("assistant", avatar="✨"):
        st.markdown(bot_response)
    st.session_state.messages.append({"role": "assistant", "content": bot_response})