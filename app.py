import os
import tempfile
import streamlit as st
from rag_engine import DocumentAgentEngine

# Streamlit Page Config
st.set_page_config(
    page_title="DataBriks IA - Inteligencia Artificial Corporativa",
    page_icon="🤖",
    layout="wide"
)


# Custom CSS for modern UI design
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: #38bdf8;
    }
    .main-header p {
        color: #94a3b8;
        font-size: 1.05rem;
    }
    .badge-gcp {
        background-color: #4285F4;
        color: white;
        padding: 0.25rem 0.6rem;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .source-box {
        background-color: #1e293b;
        border-left: 4px solid #38bdf8;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 4px;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Header Section
st.markdown("""
<div class="main-header">
    <h1>🤖 DataBriks IA <span class="badge-gcp">Cloud Run / GCP Activo</span></h1>
    <p>Asistente virtual para consulta instantánea de documentos corporativos (PDF, CSV, Excel XLSX, TXT, MD)</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/google-cloud-platform.png", width=60)
    
    
    api_key = st.text_input(
        "Gemini API Key",
        value=os.environ.get("GEMINI_API_KEY", ""),
        type="password",
        help="Obtén tu API key gratuita en Google AI Studio (aistudio.google.com)"
    )
    
    st.divider()
    st.subheader("Documentación Corporativa")
    
    doc_source = st.radio(
        "Selecciona el origen del documento:",
        ["Subir Archivo", "(Demo)"],
        index=0
    )
    
    selected_file_path = None
    selected_file_name = None

    if doc_source == "(Demo)":
        sample_choice = st.selectbox(
            "Elije un documento de prueba:",
            [
                "manual_tecnologia_y_politicas.md (PDF/Markdown Tecnologías)",
                "documentacion_saas_plataforma.md (SaaS: Precios, FAQ y Términos)",
                "reporte_presupuestos_2026.xlsx (Excel Hoja de Cálculo)",
                "datos_ventas_2015.csv (CSV Reporte Ventas)"
            ]
        )
        if "manual_tecnologia_y_politicas.md" in sample_choice:
            selected_file_path = os.path.join("sample_data", "manual_tecnologia_y_politicas.md")
            selected_file_name = "manual_tecnologia_y_politicas.md"
        elif "documentacion_saas_plataforma.md" in sample_choice:
            selected_file_path = os.path.join("sample_data", "documentacion_saas_plataforma.md")
            selected_file_name = "documentacion_saas_plataforma.md"
        elif "reporte_presupuestos_2026.xlsx" in sample_choice:
            selected_file_path = os.path.join("sample_data", "reporte_presupuestos_2026.xlsx")
            selected_file_name = "reporte_presupuestos_2026.xlsx"
        else:
            selected_file_path = os.path.join("sample_data", "datos_ventas_2015.csv")
            selected_file_name = "datos_ventas_2015.csv"

    else:
        uploaded_file = st.file_uploader(
            "Carga un archivo ",
            type=["pdf", "csv", "txt", "md", "xlsx", "xls"]
        )
        if uploaded_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                tmp.write(uploaded_file.getvalue())
                selected_file_path = tmp.name
            selected_file_name = uploaded_file.name

    process_btn = st.button("🚀 Indexar Documento", type="primary", use_container_width=True)

# State initialization
if "agent_engine" not in st.session_state:
    st.session_state.agent_engine = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "indexed_doc_name" not in st.session_state:
    st.session_state.indexed_doc_name = None

# Document Processing Logic
if process_btn:
    if not api_key:
        st.error("⚠️ Por favor ingresa tu Gemini API Key en la barra lateral.")
    elif not selected_file_path or not os.path.exists(selected_file_path):
        st.warning("⚠️ Selecciona o sube un documento válido antes de continuar.")
    else:
        with st.spinner("Procesando documento e indexando en FAISS vectorstore..."):
            try:
                engine = DocumentAgentEngine(api_key=api_key)
                status_msg = engine.load_and_index_document(selected_file_path, selected_file_name)
                st.session_state.agent_engine = engine
                st.session_state.indexed_doc_name = selected_file_name
                st.success(f"✅ {status_msg}")
            except Exception as e:
                error_msg = str(e)
                if "API key" in error_msg.lower() or "invalid" in error_msg.lower():
                    st.error("⚠️ La API key de Gemini no es válida. Revisa la clave en la barra lateral o en el archivo .env y vuelve a intentarlo.")
                else:
                    st.error(f"Error procesando el documento: {error_msg}")

# Active Document Banner
if st.session_state.indexed_doc_name:
    st.info(f"📄 **Documento Activo:** `{st.session_state.indexed_doc_name}` | Listo para responder preguntas.")

    preset_q = None
    if doc_source == "(Demo)":
        st.markdown("### Preguntas Sugeridas de Prueba:")
        col1, col2, col3 = st.columns(3)

        if "manual_tecnologia" in st.session_state.indexed_doc_name:
            with col1:
                if st.button("💻 ¿Qué lenguajes usan en el back-end?"):
                    preset_q = "¿Qué lenguajes de programación se usan en el back-end de la plataforma de ventas de la empresa?"
            with col2:
                if st.button("☁️ ¿En qué nube está alojada la infraestructura?"):
                    preset_q = "¿En qué plataforma cloud y servicios se aloja la infraestructura de la empresa?"
            with col3:
                if st.button("🎓 ¿Cuál es el presupuesto educativo?"):
                    preset_q = "¿Cuál es el presupuesto anual para capacitaciones y cursos?"
        elif "saas" in st.session_state.indexed_doc_name.lower():
            with col1:
                if st.button("💳 ¿Qué planes y precios ofrecen?"):
                    preset_q = "¿Cuáles son los planes y precios mensuales disponibles en la plataforma?"
            with col2:
                if st.button("🔒 ¿Cómo protegen la privacidad de los datos de IA?"):
                    preset_q = "¿Los documentos cargados en el agente de IA se usan para entrenar modelos públicos?"
            with col3:
                if st.button("⏱️ ¿Cuál es la política de reembolso y SLA?"):
                    preset_q = "¿Cuál es el SLA de disponibilidad garantizado y la política de reembolso?"
        elif "xlsx" in st.session_state.indexed_doc_name.lower() or "presupuesto" in st.session_state.indexed_doc_name.lower():
            with col1:
                if st.button("📈 ¿Cuál es el departamento con mayor presupuesto?"):
                    preset_q = "¿Cuál es el departamento con mayor presupuesto asignado para 2026 y cuál es el monto?"
            with col2:
                if st.button("👤 ¿Quién es el responsable de Ventas & LATAM?"):
                    preset_q = "¿Quién es la persona responsable del departamento de Ventas & LATAM?"
            with col3:
                if st.button("💰 ¿Cuál es el presupuesto de Recursos Humanos?"):
                    preset_q = "¿Cuál es el presupuesto asignado a Recursos Humanos?"
        else:
            with col1:
                if st.button("📊 ¿Cuál fue el producto más vendido en dic 2015?"):
                    preset_q = "¿Cuál fue el producto más vendido o con mayores ventas en diciembre de 2015?"
            with col2:
                if st.button("💰 ¿Quién fue el vendedor con más ventas?"):
                    preset_q = "¿Qué vendedores registraron mayores ventas en diciembre de 2015?"
            with col3:
                if st.button("📈 ¿Qué categorías de productos hay?"):
                    preset_q = "¿Qué categorías de productos se vendieron en diciembre de 2015?"

    # Render previous messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User Input Chat Box
    user_input = st.chat_input("Escribe tu pregunta sobre el documento aquí...") or preset_q

    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Alura Agente consultando el documento..."):
                result = st.session_state.agent_engine.answer_question(user_input)
                answer = result["answer"]
                sources = result["sources"]

                st.markdown(answer)
                
                # Show sources inside an expander
                if sources:
                    with st.expander("🔍 Ver fragmentos de fuente consultados"):
                        for i, src in enumerate(sources, 1):
                            st.markdown(f"**Fragmento {i}:**")
                            st.code(src, language="text")

                st.session_state.messages.append({"role": "assistant", "content": answer})

else:
    st.warning("Para comenzar, selecciona un documento de prueba o sube tu propio archivo desde la barra lateral izquierda y haz clic en **Indexar Documento**.")
